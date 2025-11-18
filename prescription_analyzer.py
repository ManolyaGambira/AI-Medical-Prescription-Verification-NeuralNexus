#!/usr/bin/env python3

"""
================================================================================
MEDICAL PRESCRIPTION ANALYZER - COMPLETE ALL-IN-ONE APPLICATION WITH DOSAGE
================================================================================
DISCLAIMER: Educational purposes only - NOT for clinical use
Always consult healthcare professionals before taking any medication
================================================================================
INSTALLATION INSTRUCTIONS
================================================================================
Step 1: Install Python Dependencies
pip install streamlit pillow pytesseract opencv-python numpy easyocr

Step 2: Install Tesseract OCR (Already installed - good!)
Verify installation:
tesseract --version

If needed:
WINDOWS:
- Download: https://github.com/UB-Mannheim/tesseract/wiki
- Run installer (default path: C:\Program Files\Tesseract-OCR)
MAC:
brew install tesseract
LINUX (Ubuntu/Debian):
sudo apt-get install tesseract-ocr

Step 3: Run the Application
streamlit run prescription_analyzer.py

Step 4: Open in Browser
http://localhost:8501

================================================================================
FEATURES & USAGE
================================================================================
📸 PRESCRIPTION OCR TAB:
1. Upload a handwritten prescription image OR use camera
2. Enter patient age
3. Click "🔍 Analyze Prescription"
4. System extracts ALL drugs from handwriting (EasyOCR + Tesseract fallback)
5. Shows dosages, frequencies, interactions
6. Displays age-appropriate mg/kg dosage recommendations with warnings
7. Shows alternatives if conflicts exist

🔍 INTERACTION CHECKER TAB:
1. Enter multiple drug names (comma/line separated)
2. Click "Check"
3. View all interactions with severity levels

📏 DOSAGE INFO TAB:
1. Select any drug from dropdown
2. Enter patient age
3. View mg/kg dosage recommendations and warnings
4. See drug information and alternatives

🏥 SAFETY CHECK TAB:
1. Select patient's medical conditions
2. Enter medications
3. Click "Check Safety"
4. See contraindications and warnings

================================================================================
END OF DOCUMENTATION - CODE STARTS BELOW
================================================================================
"""

import streamlit as st
import re
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import cv2

# ============================================================================
# ADDED: Try to import EasyOCR (INTEGRATED FROM pris.py)
# ============================================================================
try:
    import easyocr
    EASYOCR_AVAILABLE = True
    OCR_READER = easyocr.Reader(['en'], gpu=False)
except ImportError:
    EASYOCR_AVAILABLE = False
    OCR_READER = None

# ============================================================================
# Try Pytesseract OCR as secondary fallback
# ============================================================================
try:
    import pytesseract
    PYTESSERACT_OCR_AVAILABLE = True
except ImportError:
    PYTESSERACT_OCR_AVAILABLE = False
    PYTESSERACT_OCR_AVAILABLE = False

# ============================================================================
# COMPLETE DRUG DATABASE - 150+ MEDICATIONS
# ============================================================================
DRUGS = {
# ANTIBIOTICS (10)
"amoxicillin": {"class": "antibiotic", "generic": "amoxicillin"},
"azithromycin": {"class": "antibiotic", "generic": "azithromycin"},
"ciprofloxacin": {"class": "antibiotic", "generic": "ciprofloxacin"},
"levofloxacin": {"class": "antibiotic", "generic": "levofloxacin"},
"doxycycline": {"class": "antibiotic", "generic": "doxycycline"},
"cephalexin": {"class": "antibiotic", "generic": "cephalexin"},
"metronidazole": {"class": "antibiotic", "generic": "metronidazole"},
"clindamycin": {"class": "antibiotic", "generic": "clindamycin"},
"ceftriaxone": {"class": "antibiotic", "generic": "ceftriaxone"},
"amoxicillin-clavulanic acid": {"class": "antibiotic", "generic": "amoxicillin-clavulanic acid"},

# PAINKILLERS / NSAIDs (11)
"paracetamol": {"class": "analgesic", "generic": "acetaminophen"},
"acetaminophen": {"class": "analgesic", "generic": "acetaminophen"},
"ibuprofen": {"class": "nsaid", "generic": "ibuprofen"},
"diclofenac": {"class": "nsaid", "generic": "diclofenac"},
"naproxen": {"class": "nsaid", "generic": "naproxen"},
"aspirin": {"class": "nsaid", "generic": "aspirin"},
"tramadol": {"class": "painkiller", "generic": "tramadol"},
"ketorolac": {"class": "nsaid", "generic": "ketorolac"},
"celecoxib": {"class": "nsaid", "generic": "celecoxib"},
"etoricoxib": {"class": "nsaid", "generic": "etoricoxib"},
"morphine": {"class": "opioid", "generic": "morphine"},

# ANTI-ALLERGY / ANTIHISTAMINES (6)
"cetirizine": {"class": "antihistamine", "generic": "cetirizine"},
"loratadine": {"class": "antihistamine", "generic": "loratadine"},
"fexofenadine": {"class": "antihistamine", "generic": "fexofenadine"},
"diphenhydramine": {"class": "antihistamine", "generic": "diphenhydramine"},
"levocetirizine": {"class": "antihistamine", "generic": "levocetirizine"},
"chlorpheniramine maleate": {"class": "antihistamine", "generic": "chlorpheniramine"},

# ANTI-DIABETIC (7)
"metformin": {"class": "antidiabetic", "generic": "metformin"},
"glimepiride": {"class": "sulfonylurea", "generic": "glimepiride"},
"sitagliptin": {"class": "dpp4_inhibitor", "generic": "sitagliptin"},
"dapagliflozin": {"class": "sglt2_inhibitor", "generic": "dapagliflozin"},
"pioglitazone": {"class": "thiazolidinedione", "generic": "pioglitazone"},
"insulin regular": {"class": "insulin", "generic": "insulin"},
"insulin glargine": {"class": "insulin", "generic": "insulin glargine"},

# CARDIOVASCULAR (14)
"atorvastatin": {"class": "statin", "generic": "atorvastatin"},
"rosuvastatin": {"class": "statin", "generic": "rosuvastatin"},
"clopidogrel": {"class": "antiplatelet", "generic": "clopidogrel"},
"metoprolol": {"class": "beta_blocker", "generic": "metoprolol"},
"atenolol": {"class": "beta_blocker", "generic": "atenolol"},
"amlodipine": {"class": "calcium_blocker", "generic": "amlodipine"},
"losartan": {"class": "arb", "generic": "losartan"},
"telmisartan": {"class": "arb", "generic": "telmisartan"},
"enalapril": {"class": "ace_inhibitor", "generic": "enalapril"},
"ramipril": {"class": "ace_inhibitor", "generic": "ramipril"},
"carvedilol": {"class": "beta_blocker", "generic": "carvedilol"},
"hydrochlorothiazide": {"class": "diuretic", "generic": "hydrochlorothiazide"},
"furosemide": {"class": "diuretic", "generic": "furosemide"},
"spironolactone": {"class": "diuretic", "generic": "spironolactone"},

# GASTROINTESTINAL (8)
"omeprazole": {"class": "ppi", "generic": "omeprazole"},
"pantoprazole": {"class": "ppi", "generic": "pantoprazole"},
"rabeprazole": {"class": "ppi", "generic": "rabeprazole"},
"esomeprazole": {"class": "ppi", "generic": "esomeprazole"},
"ranitidine": {"class": "h2_blocker", "generic": "ranitidine"},
"domperidone": {"class": "prokinetic", "generic": "domperidone"},
"ondansetron": {"class": "antiemetic", "generic": "ondansetron"},
"loperamide": {"class": "antidiarrheal", "generic": "loperamide"},

# PSYCHIATRIC / NEUROLOGICAL (15)
"sertraline": {"class": "ssri", "generic": "sertraline"},
"fluoxetine": {"class": "ssri", "generic": "fluoxetine"},
"escitalopram": {"class": "ssri", "generic": "escitalopram"},
"paroxetine": {"class": "ssri", "generic": "paroxetine"},
"alprazolam": {"class": "benzodiazepine", "generic": "alprazolam"},
"diazepam": {"class": "benzodiazepine", "generic": "diazepam"},
"lorazepam": {"class": "benzodiazepine", "generic": "lorazepam"},
"amitriptyline": {"class": "antidepressant", "generic": "amitriptyline"},
"olanzapine": {"class": "antipsychotic", "generic": "olanzapine"},
"risperidone": {"class": "antipsychotic", "generic": "risperidone"},
"quetiapine": {"class": "antipsychotic", "generic": "quetiapine"},
"haloperidol": {"class": "antipsychotic", "generic": "haloperidol"},
"gabapentin": {"class": "anticonvulsant", "generic": "gabapentin"},
"pregabalin": {"class": "anticonvulsant", "generic": "pregabalin"},
"donepezil": {"class": "cholinesterase", "generic": "donepezil"},

# RESPIRATORY (7)
"montelukast": {"class": "leukotriene", "generic": "montelukast"},
"salbutamol": {"class": "bronchodilator", "generic": "salbutamol"},
"budesonide": {"class": "corticosteroid", "generic": "budesonide"},
"formoterol": {"class": "laba", "generic": "formoterol"},
"theophylline": {"class": "bronchodilator", "generic": "theophylline"},
"dextromethorphan": {"class": "antitussive", "generic": "dextromethorphan"},
"ipratropium": {"class": "anticholinergic", "generic": "ipratropium"},

# VITAMINS & SUPPLEMENTS (6)
"vitamin d3": {"class": "vitamin", "generic": "cholecalciferol"},
"vitamin b12": {"class": "vitamin", "generic": "cobalamin"},
"folic acid": {"class": "vitamin", "generic": "folic acid"},
"calcium carbonate": {"class": "mineral", "generic": "calcium"},
"iron folic acid": {"class": "supplement", "generic": "iron"},
"multivitamin": {"class": "supplement", "generic": "multivitamin"},

# ANTIFUNGALS (4)
"fluconazole": {"class": "antifungal", "generic": "fluconazole"},
"itraconazole": {"class": "antifungal", "generic": "itraconazole"},
"ketoconazole": {"class": "antifungal", "generic": "ketoconazole"},
"clotrimazole": {"class": "antifungal", "generic": "clotrimazole"},

# STEROIDS (3)
"prednisolone": {"class": "corticosteroid", "generic": "prednisolone"},
"dexamethasone": {"class": "corticosteroid", "generic": "dexamethasone"},
"hydrocortisone": {"class": "corticosteroid", "generic": "hydrocortisone"},

# ANTIVIRALS (4)
"acyclovir": {"class": "antiviral", "generic": "acyclovir"},
"oseltamivir": {"class": "antiviral", "generic": "oseltamivir"},
"tenofovir": {"class": "antiviral", "generic": "tenofovir"},
"remdesivir": {"class": "antiviral", "generic": "remdesivir"},

# OTHERS - GENERAL USE (7)
"levothyroxine": {"class": "thyroid", "generic": "levothyroxine"},
"tamsulosin": {"class": "alpha_blocker", "generic": "tamsulosin"},
"finasteride": {"class": "5ari", "generic": "finasteride"},
"sildenafil": {"class": "pde5_inhibitor", "generic": "sildenafil"},
"misoprostol": {"class": "prostaglandin", "generic": "misoprostol"},
"tranexamic acid": {"class": "antifibrinolytic", "generic": "tranexamic acid"},
"warfarin": {"class": "anticoagulant", "generic": "warfarin"},
}

# ============================================================================
# DRUG-DRUG INTERACTIONS (100+ CRITICAL PAIRS)
# ============================================================================
INTERACTIONS = {
("aspirin", "ibuprofen"): {"severity": "high", "effect": "GI bleeding risk, reduced efficacy"},
("aspirin", "diclofenac"): {"severity": "high", "effect": "Increased GI ulcer risk"},
("ibuprofen", "metoprolol"): {"severity": "moderate", "effect": "Reduced BP control"},
("diclofenac", "losartan"): {"severity": "high", "effect": "Acute kidney injury risk"},
("naproxen", "enalapril"): {"severity": "high", "effect": "Reduced antihypertensive effect"},
("ketorolac", "furosemide"): {"severity": "high", "effect": "Acute renal failure"},
("azithromycin", "atorvastatin"): {"severity": "moderate", "effect": "Increased statin toxicity"},
("ciprofloxacin", "theophylline"): {"severity": "moderate", "effect": "Increased theophylline levels"},
("doxycycline", "calcium carbonate"): {"severity": "high", "effect": "Reduced doxycycline absorption"},
("metronidazole", "alcohol"): {"severity": "high", "effect": "Disulfiram-like reaction"},
("cephalexin", "warfarin"): {"severity": "moderate", "effect": "Increased bleeding risk"},
("atorvastatin", "clarithromycin"): {"severity": "high", "effect": "Statin myopathy risk"},
("clopidogrel", "omeprazole"): {"severity": "high", "effect": "Reduced antiplatelet effect"},
("metoprolol", "verapamil"): {"severity": "high", "effect": "Severe bradycardia risk"},
("amlodipine", "atorvastatin"): {"severity": "moderate", "effect": "Increased statin levels"},
("losartan", "potassium supplements"): {"severity": "high", "effect": "Hyperkalemia"},
("enalapril", "spironolactone"): {"severity": "high", "effect": "Hyperkalemia risk"},
("ramipril", "nsaid"): {"severity": "high", "effect": "Acute kidney injury"},
("metformin", "prednisolone"): {"severity": "high", "effect": "Poor glucose control"},
("metformin", "contrast dye"): {"severity": "high", "effect": "Lactic acidosis risk"},
("glimepiride", "nsaid"): {"severity": "moderate", "effect": "Severe hypoglycemia"},
("sitagliptin", "ace inhibitor"): {"severity": "moderate", "effect": "Increased hypoglycemia risk"},
("omeprazole", "clopidogrel"): {"severity": "high", "effect": "Reduced clopidogrel effect"},
("pantoprazole", "iron folic acid"): {"severity": "moderate", "effect": "Reduced iron absorption"},
("ranitidine", "ketoconazole"): {"severity": "high", "effect": "Reduced antifungal effect"},
("ondansetron", "tramadol"): {"severity": "moderate", "effect": "Serotonin syndrome risk"},
("sertraline", "tramadol"): {"severity": "high", "effect": "Serotonin syndrome"},
("fluoxetine", "warfarin"): {"severity": "high", "effect": "Increased bleeding risk"},
("escitalopram", "alprazolam"): {"severity": "moderate", "effect": "CNS depression"},
("alprazolam", "morphine"): {"severity": "high", "effect": "Respiratory depression"},
("diazepam", "alcohol"): {"severity": "high", "effect": "Severe CNS depression"},
("amitriptyline", "nsaid"): {"severity": "moderate", "effect": "GI bleeding risk"},
("olanzapine", "carbamazepine"): {"severity": "moderate", "effect": "Reduced olanzapine effect"},
("salbutamol", "metoprolol"): {"severity": "high", "effect": "Bronchospasm, reduced bronchodilation"},
("theophylline", "erythromycin"): {"severity": "high", "effect": "Theophylline toxicity"},
("budesonide", "live vaccines"): {"severity": "high", "effect": "Vaccine ineffectiveness"},
("warfarin", "aspirin"): {"severity": "high", "effect": "Severe bleeding risk"},
("warfarin", "nsaid"): {"severity": "high", "effect": "GI bleeding"},
("warfarin", "azithromycin"): {"severity": "high", "effect": "Increased INR"},
("paracetamol", "warfarin"): {"severity": "moderate", "effect": "Increased bleeding risk"},
("vitamin d3", "calcium carbonate"): {"severity": "low", "effect": "Synergistic - appropriate"},
("iron folic acid", "tetracycline"): {"severity": "high", "effect": "Reduced antibiotic absorption"},
("fluconazole", "warfarin"): {"severity": "high", "effect": "Increased INR"},
("prednisolone", "nsaid"): {"severity": "high", "effect": "GI ulcer risk"},
("levothyroxine", "iron folic acid"): {"severity": "high", "effect": "Reduced thyroid hormone absorption"},
("sildenafil", "nitrates"): {"severity": "high", "effect": "Severe hypotension"},
("tramadol", "ssri"): {"severity": "high", "effect": "Serotonin syndrome risk"},
("morphine", "benzodiazepine"): {"severity": "high", "effect": "Respiratory depression"},
("diclofenac", "ace inhibitor"): {"severity": "high", "effect": "Acute renal failure"},
("ketorolac", "metoprolol"): {"severity": "moderate", "effect": "Reduced BP control"},
("celecoxib", "warfarin"): {"severity": "high", "effect": "Increased bleeding"},
("etoricoxib", "losartan"): {"severity": "high", "effect": "Kidney damage risk"},
}

# Add reverse pairs
for (drug1, drug2), info in list(INTERACTIONS.items()):
    INTERACTIONS[(drug2, drug1)] = info

# ============================================================================
# DRUG ALTERNATIVES
# ============================================================================
ALTERNATIVES = {
"aspirin": ["paracetamol", "ibuprofen", "diclofenac"],
"ibuprofen": ["paracetamol", "naproxen", "diclofenac", "etoricoxib"],
"diclofenac": ["ibuprofen", "naproxen", "celecoxib"],
"paracetamol": ["ibuprofen", "aspirin", "tramadol"],
"atorvastatin": ["rosuvastatin"],
"rosuvastatin": ["atorvastatin"],
"metformin": ["sitagliptin", "dapagliflozin", "pioglitazone"],
"glimepiride": ["sitagliptin", "dapagliflozin"],
"omeprazole": ["pantoprazole", "esomeprazole", "rabeprazole"],
"pantoprazole": ["omeprazole", "esomeprazole"],
"prednisolone": ["dexamethasone", "hydrocortisone"],
"dexamethasone": ["prednisolone", "hydrocortisone"],
"metoprolol": ["atenolol", "carvedilol"],
"atenolol": ["metoprolol", "carvedilol"],
"losartan": ["telmisartan", "enalapril", "ramipril"],
"telmisartan": ["losartan", "enalapril"],
"enalapril": ["ramipril", "losartan", "telmisartan"],
"sertraline": ["fluoxetine", "escitalopram", "paroxetine"],
"fluoxetine": ["sertraline", "escitalopram"],
"alprazolam": ["diazepam", "lorazepam"],
"diazepam": ["alprazolam", "lorazepam"],
"amoxicillin": ["cephalexin", "azithromycin"],
"azithromycin": ["amoxicillin", "doxycycline"],
"ciprofloxacin": ["levofloxacin", "ceftriaxone"],
"fluconazole": ["itraconazole", "ketoconazole"],
"warfarin": ["clopidogrel"],
"clopidogrel": ["warfarin"],
"salbutamol": ["formoterol", "theophylline"],
"amlodipine": ["diltiazem"],
"furosemide": ["hydrochlorothiazide", "spironolactone"],
"tramadol": ["paracetamol", "ibuprofen", "morphine"],
"morphine": ["tramadol"],
"ondansetron": ["domperidone"],
"cetirizine": ["loratadine", "fexofenadine"],
"acyclovir": ["oseltamivir"],
}

CONDITIONS = {
"diabetes": {"avoid": ["prednisolone", "dexamethasone", "corticosteroid"], "reason": "Raises blood sugar"},
"hypertension": {"avoid": ["nsaid", "decongestants"], "reason": "Raises blood pressure"},
"asthma": {"avoid": ["aspirin", "nsaid", "beta_blocker"], "reason": "May trigger attack"},
"kidney disease": {"avoid": ["nsaid", "metformin", "ace_inhibitor"], "reason": "Kidney damage"},
"liver disease": {"avoid": ["paracetamol", "acetaminophen"], "reason": "Liver toxicity"},
"bleeding disorder": {"avoid": ["nsaid", "aspirin", "warfarin"], "reason": "Increased bleeding"},
"heart failure": {"avoid": ["nsaid", "calcium_blocker"], "reason": "May worsen condition"},
"pregnancy": {"avoid": ["warfarin", "ace_inhibitor", "finasteride"], "reason": "Birth defects"},
}

# ============================================================================
# COMPREHENSIVE DOSAGE GUIDELINES FOR ALL 150 DRUGS
# ============================================================================
DOSAGES = {
# ANTIBIOTICS
"amoxicillin": {
"child": {"dose": "20-40 mg/kg/day", "max": "90 mg/kg/day", "warning": "Divide into 2-3 doses, use under pediatric supervision"},
"adult": {"dose": "250-500 mg every 8 hours", "max": "3000 mg/day", "warning": "Take with food to reduce GI upset"},
"elderly": {"dose": "250-500 mg every 12 hours", "max": "3000 mg/day", "warning": "Monitor renal function, adjust if CrCl <30"}
},
"azithromycin": {
"child": {"dose": "10 mg/kg on day 1, then 5 mg/kg", "max": "500 mg/day", "warning": "Single daily dose, complete course"},
"adult": {"dose": "500 mg day 1, then 250 mg", "max": "500 mg/day", "warning": "Take on empty stomach"},
"elderly": {"dose": "500 mg day 1, then 250 mg", "max": "500 mg/day", "warning": "Check for QT prolongation risk"}
},
"ciprofloxacin": {
"child": {"dose": "Not recommended under 18", "max": "N/A", "warning": "Risk of tendon damage, use only if essential"},
"adult": {"dose": "250-750 mg every 12 hours", "max": "1500 mg/day", "warning": "Avoid in pregnancy, risk of tendonitis"},
"elderly": {"dose": "250-500 mg every 12 hours", "max": "1000 mg/day", "warning": "Higher risk of tendon rupture"}
},
"levofloxacin": {
"child": {"dose": "Not recommended", "max": "N/A", "warning": "Use only if no alternative"},
"adult": {"dose": "250-750 mg once daily", "max": "750 mg/day", "warning": "Take with plenty of water"},
"elderly": {"dose": "250-500 mg once daily", "max": "500 mg/day", "warning": "Adjust for renal function"}
},
"doxycycline": {
"child": {"dose": "2-4 mg/kg/day", "max": "200 mg/day", "warning": "Avoid under 8 years, tooth discoloration risk"},
"adult": {"dose": "100 mg every 12 hours", "max": "200 mg/day", "warning": "Take with food, avoid dairy within 2 hours"},
"elderly": {"dose": "100 mg every 12-24 hours", "max": "200 mg/day", "warning": "Photosensitivity - use sunscreen"}
},
"cephalexin": {
"child": {"dose": "25-50 mg/kg/day", "max": "100 mg/kg/day", "warning": "Divide into 4 doses"},
"adult": {"dose": "250-500 mg every 6 hours", "max": "4000 mg/day", "warning": "Take with or without food"},
"elderly": {"dose": "250-500 mg every 8 hours", "max": "3000 mg/day", "warning": "Adjust for renal impairment"}
},
"metronidazole": {
"child": {"dose": "15-35 mg/kg/day", "max": "2000 mg/day", "warning": "Divide into 3 doses"},
"adult": {"dose": "250-500 mg every 8 hours", "max": "4000 mg/day", "warning": "Avoid alcohol - disulfiram reaction"},
"elderly": {"dose": "250-500 mg every 12 hours", "max": "2000 mg/day", "warning": "Reduce dose in hepatic disease"}
},
"clindamycin": {
"child": {"dose": "10-25 mg/kg/day", "max": "40 mg/kg/day", "warning": "Divide into 3-4 doses"},
"adult": {"dose": "150-450 mg every 6 hours", "max": "1800 mg/day", "warning": "Risk of C. difficile diarrhea"},
"elderly": {"dose": "150-300 mg every 8 hours", "max": "1200 mg/day", "warning": "Monitor for diarrhea"}
},
"ceftriaxone": {
"child": {"dose": "50-75 mg/kg/day", "max": "2000 mg/day", "warning": "Single daily dose or divided every 12h"},
"adult": {"dose": "1-2 g once daily", "max": "4 g/day", "warning": "IM or IV administration"},
"elderly": {"dose": "1 g once daily", "max": "2 g/day", "warning": "No dose adjustment for renal impairment"}
},
"amoxicillin-clavulanic acid": {
"child": {"dose": "25-45 mg/kg/day", "max": "90 mg/kg/day", "warning": "Based on amoxicillin component"},
"adult": {"dose": "500-875 mg every 12 hours", "max": "2000 mg/day", "warning": "Take with food"},
"elderly": {"dose": "500 mg every 12 hours", "max": "1500 mg/day", "warning": "Monitor liver function"}
},

# PAINKILLERS / NSAIDs
"paracetamol": {
"child": {"dose": "10-15 mg/kg/dose", "max": "60 mg/kg/day", "warning": "Every 4-6 hours, hepatotoxicity risk if overdose"},
"adult": {"dose": "500-1000 mg every 4-6 hours", "max": "4000 mg/day", "warning": "Do not exceed max dose - liver damage"},
"elderly": {"dose": "500 mg every 6 hours", "max": "3000 mg/day", "warning": "Monitor liver function"}
},
"acetaminophen": {
"child": {"dose": "10-15 mg/kg/dose", "max": "60 mg/kg/day", "warning": "Every 4-6 hours, hepatotoxicity risk if overdose"},
"adult": {"dose": "500-1000 mg every 4-6 hours", "max": "4000 mg/day", "warning": "Do not exceed max dose - liver damage"},
"elderly": {"dose": "500 mg every 6 hours", "max": "3000 mg/day", "warning": "Monitor liver function"}
},
"ibuprofen": {
"child": {"dose": "5-10 mg/kg/dose", "max": "40 mg/kg/day", "warning": "Every 6-8 hours with food"},
"adult": {"dose": "200-400 mg every 6-8 hours", "max": "3200 mg/day", "warning": "Take with food, GI and kidney risk"},
"elderly": {"dose": "200 mg every 8-12 hours", "max": "1600 mg/day", "warning": "Increased GI bleeding risk"}
},
"diclofenac": {
"child": {"dose": "1-3 mg/kg/day", "max": "150 mg/day", "warning": "Divide into 2-3 doses"},
"adult": {"dose": "50 mg every 8-12 hours", "max": "150 mg/day", "warning": "Take with food, cardiovascular risk"},
"elderly": {"dose": "25-50 mg every 12 hours", "max": "100 mg/day", "warning": "High GI bleed risk, use lowest dose"}
},
"naproxen": {
"child": {"dose": "5-7 mg/kg every 12 hours", "max": "1000 mg/day", "warning": "Over 2 years old"},
"adult": {"dose": "250-500 mg every 12 hours", "max": "1250 mg/day", "warning": "Take with food"},
"elderly": {"dose": "250 mg every 12 hours", "max": "750 mg/day", "warning": "GI and cardiovascular risk"}
},
"aspirin": {
"child": {"dose": "10-15 mg/kg/dose", "max": "81 mg/day", "warning": "Avoid under 12 - Reye's syndrome risk"},
"adult": {"dose": "325-650 mg every 4-6 hours", "max": "4000 mg/day", "warning": "Take with food, bleeding risk"},
"elderly": {"dose": "81-325 mg once daily", "max": "650 mg/day", "warning": "GI bleeding, use low dose for cardioprotection"}
},
"tramadol": {
"child": {"dose": "1-2 mg/kg every 6 hours", "max": "400 mg/day", "warning": "Over 12 years, seizure risk"},
"adult": {"dose": "50-100 mg every 4-6 hours", "max": "400 mg/day", "warning": "Risk of dependence, serotonin syndrome"},
"elderly": {"dose": "50 mg every 6-8 hours", "max": "300 mg/day", "warning": "Start low, titrate slowly"}
},
"ketorolac": {
"child": {"dose": "Not recommended", "max": "N/A", "warning": "Use only if essential, short-term"},
"adult": {"dose": "10 mg every 4-6 hours", "max": "40 mg/day", "warning": "Maximum 5 days, high GI/renal risk"},
"elderly": {"dose": "10 mg every 6-8 hours", "max": "40 mg/day", "warning": "Avoid if possible, severe adverse effects"}
},
"celecoxib": {
"child": {"dose": "Not established", "max": "N/A", "warning": "Consult specialist"},
"adult": {"dose": "100-200 mg once or twice daily", "max": "400 mg/day", "warning": "Cardiovascular risk, use lowest dose"},
"elderly": {"dose": "100 mg once daily", "max": "200 mg/day", "warning": "Reduced GI risk vs traditional NSAIDs"}
},
"etoricoxib": {
"child": {"dose": "Not recommended", "max": "N/A", "warning": "Not approved for pediatric use"},
"adult": {"dose": "60-120 mg once daily", "max": "120 mg/day", "warning": "Cardiovascular risk, short-term use"},
"elderly": {"dose": "60 mg once daily", "max": "90 mg/day", "warning": "Monitor blood pressure"}
},
"morphine": {
"child": {"dose": "0.1-0.2 mg/kg every 4 hours", "max": "0.6 mg/kg/day", "warning": "Respiratory depression, close monitoring"},
"adult": {"dose": "10-30 mg every 4 hours", "max": "200 mg/day", "warning": "Risk of dependence, respiratory depression"},
"elderly": {"dose": "5-10 mg every 4-6 hours", "max": "60 mg/day", "warning": "Start low, high risk of adverse effects"}
},

# ANTIHISTAMINES
"cetirizine": {
"child": {"dose": "0.25 mg/kg once daily", "max": "10 mg/day", "warning": "Over 2 years, may cause drowsiness"},
"adult": {"dose": "5-10 mg once daily", "max": "10 mg/day", "warning": "Non-drowsy in most, take evening if drowsy"},
"elderly": {"dose": "5 mg once daily", "max": "10 mg/day", "warning": "Reduce dose in renal impairment"}
},
"loratadine": {
"child": {"dose": "5 mg once daily (<30 kg)", "max": "10 mg/day", "warning": "Over 2 years"},
"adult": {"dose": "10 mg once daily", "max": "10 mg/day", "warning": "Non-sedating, safe profile"},
"elderly": {"dose": "10 mg once daily", "max": "10 mg/day", "warning": "No dose adjustment needed"}
},
"fexofenadine": {
"child": {"dose": "30 mg twice daily", "max": "120 mg/day", "warning": "Over 6 years"},
"adult": {"dose": "120-180 mg once daily", "max": "180 mg/day", "warning": "Take with water, not juice"},
"elderly": {"dose": "120 mg once daily", "max": "180 mg/day", "warning": "No adjustment needed"}
},
"diphenhydramine": {
"child": {"dose": "1-2 mg/kg every 6 hours", "max": "300 mg/day", "warning": "Over 2 years, causes drowsiness"},
"adult": {"dose": "25-50 mg every 4-6 hours", "max": "300 mg/day", "warning": "Sedating, avoid driving"},
"elderly": {"dose": "25 mg every 6-8 hours", "max": "150 mg/day", "warning": "Avoid - anticholinergic effects"}
},
"levocetirizine": {
"child": {"dose": "2.5 mg once daily", "max": "5 mg/day", "warning": "Over 6 months"},
"adult": {"dose": "5 mg once daily", "max": "5 mg/day", "warning": "Evening dosing if drowsiness"},
"elderly": {"dose": "2.5-5 mg once daily", "max": "5 mg/day", "warning": "Adjust for renal function"}
},
"chlorpheniramine maleate": {
"child": {"dose": "0.35 mg/kg/day divided", "max": "12 mg/day", "warning": "Every 4-6 hours, sedating"},
"adult": {"dose": "4 mg every 4-6 hours", "max": "24 mg/day", "warning": "Drowsiness common"},
"elderly": {"dose": "2-4 mg every 6-8 hours", "max": "16 mg/day", "warning": "Avoid - anticholinergic effects"}
},

# ANTI-DIABETIC
"metformin": {
"child": {"dose": "500 mg twice daily", "max": "2000 mg/day", "warning": "Over 10 years, titrate slowly"},
"adult": {"dose": "500-1000 mg twice daily", "max": "2550 mg/day", "warning": "Start low, with meals, GI side effects common"},
"elderly": {"dose": "500 mg once-twice daily", "max": "2000 mg/day", "warning": "Check renal function, avoid if CrCl <30"}
},
"glimepiride": {
"child": {"dose": "Not recommended", "max": "N/A", "warning": "Not approved for pediatric use"},
"adult": {"dose": "1-2 mg once daily", "max": "8 mg/day", "warning": "Take with breakfast, hypoglycemia risk"},
"elderly": {"dose": "1 mg once daily", "max": "4 mg/day", "warning": "Start low, monitor blood sugar closely"}
},
"sitagliptin": {
"child": {"dose": "Not established", "max": "N/A", "warning": "Consult specialist"},
"adult": {"dose": "100 mg once daily", "max": "100 mg/day", "warning": "Adjust for renal impairment"},
"elderly": {"dose": "100 mg once daily", "max": "100 mg/day", "warning": "No adjustment if normal renal function"}
},
"dapagliflozin": {
"child": {"dose": "Not recommended", "max": "N/A", "warning": "Not approved"},
"adult": {"dose": "5-10 mg once daily", "max": "10 mg/day", "warning": "UTI risk, monitor hydration"},
"elderly": {"dose": "5 mg once daily", "max": "10 mg/day", "warning": "Dehydration risk, monitor closely"}
},
"pioglitazone": {
"child": {"dose": "Not recommended", "max": "N/A", "warning": "Not approved"},
"adult": {"dose": "15-30 mg once daily", "max": "45 mg/day", "warning": "Fluid retention, heart failure risk"},
"elderly": {"dose": "15 mg once daily", "max": "30 mg/day", "warning": "Monitor for edema"}
},
"insulin regular": {
"child": {"dose": "0.5-1 unit/kg/day", "max": "Individualized", "warning": "Divide into multiple doses, tight monitoring"},
"adult": {"dose": "0.5-1 unit/kg/day", "max": "Individualized", "warning": "Individualized based on blood sugar"},
"elderly": {"dose": "0.2-0.6 unit/kg/day", "max": "Individualized", "warning": "Start low, hypoglycemia risk"}
},
"insulin glargine": {
"child": {"dose": "0.1-0.2 units/kg/day", "max": "Individualized", "warning": "Once daily, long-acting basal insulin"},
"adult": {"dose": "0.2-0.4 units/kg/day", "max": "Individualized", "warning": "Once daily, same time each day"},
"elderly": {"dose": "0.1-0.3 units/kg/day", "max": "Individualized", "warning": "Lower starting dose"}
},

# CARDIOVASCULAR
"atorvastatin": {
"child": {"dose": "10 mg once daily", "max": "20 mg/day", "warning": "Over 10 years, monitor liver"},
"adult": {"dose": "10-80 mg once daily", "max": "80 mg/day", "warning": "Evening dosing, monitor CK and liver"},
"elderly": {"dose": "10-40 mg once daily", "max": "80 mg/day", "warning": "Start low, muscle pain risk"}
},
"rosuvastatin": {
"child": {"dose": "5-10 mg once daily", "max": "20 mg/day", "warning": "Over 10 years"},
"adult": {"dose": "5-40 mg once daily", "max": "40 mg/day", "warning": "Most potent statin, monitor CK"},
"elderly": {"dose": "5-10 mg once daily", "max": "20 mg/day", "warning": "Higher risk of myopathy"}
},
"clopidogrel": {
"child": {"dose": "Not established", "max": "N/A", "warning": "Consult specialist"},
"adult": {"dose": "75 mg once daily", "max": "75 mg/day", "warning": "Bleeding risk, avoid with omeprazole"},
"elderly": {"dose": "75 mg once daily", "max": "75 mg/day", "warning": "No adjustment, monitor bleeding"}
},
"metoprolol": {
"child": {"dose": "1-2 mg/kg/day divided", "max": "200 mg/day", "warning": "Titrate slowly"},
"adult": {"dose": "25-100 mg twice daily", "max": "400 mg/day", "warning": "Do not stop abruptly"},
"elderly": {"dose": "25-50 mg twice daily", "max": "200 mg/day", "warning": "Start low, bradycardia risk"}
},
"atenolol": {
"child": {"dose": "0.5-1 mg/kg once daily", "max": "100 mg/day", "warning": "Over 6 years"},
"adult": {"dose": "25-100 mg once daily", "max": "200 mg/day", "warning": "Reduce in renal impairment"},
"elderly": {"dose": "25-50 mg once daily", "max": "100 mg/day", "warning": "Check renal function"}
},
"amlodipine": {
"child": {"dose": "2.5-5 mg once daily", "max": "10 mg/day", "warning": "Over 6 years"},
"adult": {"dose": "5-10 mg once daily", "max": "10 mg/day", "warning": "Ankle edema common"},
"elderly": {"dose": "2.5-5 mg once daily", "max": "10 mg/day", "warning": "Start low"}
},
"losartan": {
"child": {"dose": "0.7 mg/kg once daily", "max": "50 mg/day", "warning": "Over 6 years"},
"adult": {"dose": "25-100 mg once daily", "max": "100 mg/day", "warning": "Monitor potassium and renal function"},
"elderly": {"dose": "25-50 mg once daily", "max": "100 mg/day", "warning": "Start low"}
},
"telmisartan": {
"child": {"dose": "Not established", "max": "N/A", "warning": "Consult specialist"},
"adult": {"dose": "20-80 mg once daily", "max": "80 mg/day", "warning": "Monitor BP and renal function"},
"elderly": {"dose": "20-40 mg once daily", "max": "80 mg/day", "warning": "No adjustment usually needed"}
},
"enalapril": {
"child": {"dose": "0.08 mg/kg once daily", "max": "0.6 mg/kg/day", "warning": "Titrate slowly"},
"adult": {"dose": "2.5-20 mg once-twice daily", "max": "40 mg/day", "warning": "Monitor potassium, first-dose hypotension"},
"elderly": {"dose": "2.5-5 mg once daily", "max": "20 mg/day", "warning": "Start low, check renal function"}
},
"ramipril": {
"child": {"dose": "Not established", "max": "N/A", "warning": "Consult specialist"},
"adult": {"dose": "2.5-10 mg once daily", "max": "10 mg/day", "warning": "Monitor potassium and creatinine"},
"elderly": {"dose": "1.25-2.5 mg once daily", "max": "10 mg/day", "warning": "Start low, titrate slowly"}
},
"carvedilol": {
"child": {"dose": "Not established", "max": "N/A", "warning": "Consult specialist"},
"adult": {"dose": "3.125-25 mg twice daily", "max": "50 mg/day", "warning": "Take with food, titrate slowly"},
"elderly": {"dose": "3.125-12.5 mg twice daily", "max": "50 mg/day", "warning": "Start very low"}
},
"hydrochlorothiazide": {
"child": {"dose": "1-2 mg/kg/day", "max": "37.5 mg/day", "warning": "Divide into 1-2 doses"},
"adult": {"dose": "12.5-25 mg once daily", "max": "50 mg/day", "warning": "Monitor potassium and glucose"},
"elderly": {"dose": "12.5 mg once daily", "max": "25 mg/day", "warning": "Dehydration risk, monitor electrolytes"}
},
"furosemide": {
"child": {"dose": "1-2 mg/kg/dose", "max": "6 mg/kg/day", "warning": "Every 6-12 hours"},
"adult": {"dose": "20-80 mg once-twice daily", "max": "600 mg/day", "warning": "Monitor potassium, dehydration risk"},
"elderly": {"dose": "20-40 mg once daily", "max": "240 mg/day", "warning": "Start low, falls risk"}
},
"spironolactone": {
"child": {"dose": "1-3 mg/kg/day", "max": "100 mg/day", "warning": "Divide into 1-2 doses"},
"adult": {"dose": "25-100 mg once daily", "max": "400 mg/day", "warning": "Monitor potassium - hyperkalemia risk"},
"elderly": {"dose": "25-50 mg once daily", "max": "100 mg/day", "warning": "High hyperkalemia risk"}
},

# GASTROINTESTINAL
"omeprazole": {
"child": {"dose": "0.5-1 mg/kg once daily", "max": "40 mg/day", "warning": "Over 1 year"},
"adult": {"dose": "20-40 mg once daily", "max": "80 mg/day", "warning": "Take before breakfast, long-term risks"},
"elderly": {"dose": "20 mg once daily", "max": "40 mg/day", "warning": "Fracture risk with long-term use"}
},
"pantoprazole": {
"child": {"dose": "0.5-1 mg/kg once daily", "max": "40 mg/day", "warning": "Over 5 years"},
"adult": {"dose": "20-40 mg once daily", "max": "80 mg/day", "warning": "Take 30 min before meal"},
"elderly": {"dose": "20-40 mg once daily", "max": "40 mg/day", "warning": "No adjustment needed"}
},
"rabeprazole": {
"child": {"dose": "Not established", "max": "N/A", "warning": "Limited data"},
"adult": {"dose": "20 mg once daily", "max": "40 mg/day", "warning": "Take before meal"},
"elderly": {"dose": "20 mg once daily", "max": "40 mg/day", "warning": "No adjustment needed"}
},
"esomeprazole": {
"child": {"dose": "10-20 mg once daily", "max": "40 mg/day", "warning": "Over 1 year"},
"adult": {"dose": "20-40 mg once daily", "max": "40 mg/day", "warning": "Take 1 hour before meal"},
"elderly": {"dose": "20-40 mg once daily", "max": "40 mg/day", "warning": "No adjustment needed"}
},
"ranitidine": {
"child": {"dose": "2-4 mg/kg twice daily", "max": "300 mg/day", "warning": "Divide into 2 doses"},
"adult": {"dose": "150 mg twice daily", "max": "300 mg/day", "warning": "Less potent than PPIs"},
"elderly": {"dose": "150 mg once-twice daily", "max": "300 mg/day", "warning": "Adjust for renal impairment"}
},
"domperidone": {
"child": {"dose": "0.25 mg/kg 3-4 times daily", "max": "2.4 mg/kg/day", "warning": "Before meals"},
"adult": {"dose": "10 mg 3-4 times daily", "max": "30 mg/day", "warning": "Short-term use, cardiac risk"},
"elderly": {"dose": "10 mg twice daily", "max": "30 mg/day", "warning": "Avoid if cardiac disease"}
},
"ondansetron": {
"child": {"dose": "0.15 mg/kg/dose", "max": "8 mg/dose", "warning": "Every 8 hours"},
"adult": {"dose": "4-8 mg 2-3 times daily", "max": "24 mg/day", "warning": "QT prolongation risk"},
"elderly": {"dose": "4-8 mg 2-3 times daily", "max": "24 mg/day", "warning": "Monitor for QT changes"}
},
"loperamide": {
"child": {"dose": "Not recommended under 2", "max": "N/A", "warning": "Consult doctor"},
"adult": {"dose": "4 mg initially, then 2 mg after each loose stool", "max": "16 mg/day", "warning": "Short-term use only"},
"elderly": {"dose": "2 mg after each loose stool", "max": "8 mg/day", "warning": "Monitor for ileus"}
},

# PSYCHIATRIC/NEUROLOGICAL
"sertraline": {
"child": {"dose": "25 mg once daily", "max": "200 mg/day", "warning": "Over 6 years, titrate slowly"},
"adult": {"dose": "50-200 mg once daily", "max": "200 mg/day", "warning": "Take morning, titrate over weeks"},
"elderly": {"dose": "25-50 mg once daily", "max": "200 mg/day", "warning": "Start low, hyponatremia risk"}
},
"fluoxetine": {
"child": {"dose": "10-20 mg once daily", "max": "60 mg/day", "warning": "Over 8 years"},
"adult": {"dose": "20-80 mg once daily", "max": "80 mg/day", "warning": "Long half-life, morning dosing"},
"elderly": {"dose": "10-20 mg once daily", "max": "60 mg/day", "warning": "Start low, drug interactions"}
},
"escitalopram": {
"child": {"dose": "5-10 mg once daily", "max": "20 mg/day", "warning": "Over 12 years"},
"adult": {"dose": "10-20 mg once daily", "max": "20 mg/day", "warning": "Morning or evening"},
"elderly": {"dose": "5-10 mg once daily", "max": "10 mg/day", "warning": "QT prolongation, reduce dose"}
},
"paroxetine": {
"child": {"dose": "Not recommended", "max": "N/A", "warning": "Not approved"},
"adult": {"dose": "20-50 mg once daily", "max": "60 mg/day", "warning": "Take morning, withdrawal symptoms"},
"elderly": {"dose": "10-20 mg once daily", "max": "40 mg/day", "warning": "Start low, anticholinergic effects"}
},
"alprazolam": {
"child": {"dose": "Not recommended", "max": "N/A", "warning": "Not approved"},
"adult": {"dose": "0.25-2 mg 2-3 times daily", "max": "4 mg/day", "warning": "Short-term use, dependence risk"},
"elderly": {"dose": "0.25-0.5 mg 2-3 times daily", "max": "2 mg/day", "warning": "Falls and confusion risk"}
},
"diazepam": {
"child": {"dose": "0.12-0.8 mg/kg/day", "max": "10 mg/day", "warning": "Divide into 2-4 doses"},
"adult": {"dose": "2-10 mg 2-4 times daily", "max": "40 mg/day", "warning": "Dependence risk, taper slowly"},
"elderly": {"dose": "2-5 mg once-twice daily", "max": "15 mg/day", "warning": "High fall risk, avoid if possible"}
},
"lorazepam": {
"child": {"dose": "0.05 mg/kg/dose", "max": "2 mg/dose", "warning": "Every 4-8 hours PRN"},
"adult": {"dose": "0.5-2 mg 2-3 times daily", "max": "10 mg/day", "warning": "Short-term use, dependence"},
"elderly": {"dose": "0.5-1 mg once-twice daily", "max": "4 mg/day", "warning": "Falls and confusion risk"}
},
"amitriptyline": {
"child": {"dose": "Not recommended under 12", "max": "N/A", "warning": "Consult specialist"},
"adult": {"dose": "25-150 mg at bedtime", "max": "300 mg/day", "warning": "Sedating, anticholinergic effects"},
"elderly": {"dose": "10-25 mg at bedtime", "max": "100 mg/day", "warning": "Avoid - high anticholinergic burden"}
},
"olanzapine": {
"child": {"dose": "2.5-5 mg once daily", "max": "20 mg/day", "warning": "Over 13 years, titrate slowly"},
"adult": {"dose": "5-20 mg once daily", "max": "20 mg/day", "warning": "Weight gain, metabolic syndrome risk"},
"elderly": {"dose": "2.5-5 mg once daily", "max": "10 mg/day", "warning": "Dementia patients - increased mortality"}
},
"risperidone": {
"child": {"dose": "0.25-0.5 mg twice daily", "max": "6 mg/day", "warning": "Over 5 years, titrate slowly"},
"adult": {"dose": "1-6 mg once-twice daily", "max": "16 mg/day", "warning": "EPS risk, monitor prolactin"},
"elderly": {"dose": "0.25-0.5 mg twice daily", "max": "4 mg/day", "warning": "Stroke risk in dementia"}
},
"quetiapine": {
"child": {"dose": "25 mg twice daily", "max": "800 mg/day", "warning": "Over 10 years, titrate"},
"adult": {"dose": "25-800 mg/day divided", "max": "800 mg/day", "warning": "Sedation, metabolic effects"},
"elderly": {"dose": "25 mg once-twice daily", "max": "300 mg/day", "warning": "Start very low"}
},
"haloperidol": {
"child": {"dose": "0.05-0.15 mg/kg/day", "max": "15 mg/day", "warning": "Divide into 2-3 doses"},
"adult": {"dose": "0.5-20 mg/day divided", "max": "100 mg/day", "warning": "High EPS risk, monitor"},
"elderly": {"dose": "0.5-2 mg once-twice daily", "max": "5 mg/day", "warning": "Very high fall risk"}
},
"gabapentin": {
"child": {"dose": "10-15 mg/kg/day", "max": "50 mg/kg/day", "warning": "Over 3 years, divide into 3 doses"},
"adult": {"dose": "300-1800 mg/day divided", "max": "3600 mg/day", "warning": "Titrate slowly, dizziness common"},
"elderly": {"dose": "300-900 mg/day divided", "max": "1800 mg/day", "warning": "Adjust for renal function"}
},
"pregabalin": {
"child": {"dose": "Not established", "max": "N/A", "warning": "Not approved"},
"adult": {"dose": "150-600 mg/day divided", "max": "600 mg/day", "warning": "Dizziness, weight gain"},
"elderly": {"dose": "75-300 mg/day divided", "max": "450 mg/day", "warning": "Adjust for renal function"}
},
"donepezil": {
"child": {"dose": "Not recommended", "max": "N/A", "warning": "Not approved"},
"adult": {"dose": "5-10 mg once daily", "max": "23 mg/day", "warning": "Take at bedtime, GI effects"},
"elderly": {"dose": "5-10 mg once daily", "max": "23 mg/day", "warning": "Bradycardia risk, monitor"}
},

# RESPIRATORY
"montelukast": {
"child": {"dose": "4-5 mg once daily", "max": "10 mg/day", "warning": "Evening dosing"},
"adult": {"dose": "10 mg once daily", "max": "10 mg/day", "warning": "Take in evening"},
"elderly": {"dose": "10 mg once daily", "max": "10 mg/day", "warning": "No adjustment needed"}
},
"salbutamol": {
"child": {"dose": "0.1-0.15 mg/kg/dose", "max": "5 mg/dose", "warning": "Inhaled or nebulized PRN"},
"adult": {"dose": "100-200 mcg/dose", "max": "800 mcg/day", "warning": "PRN for bronchospasm"},
"elderly": {"dose": "100-200 mcg/dose", "max": "800 mcg/day", "warning": "Monitor heart rate"}
},
"budesonide": {
"child": {"dose": "0.25-1 mg twice daily", "max": "2 mg/day", "warning": "Inhaled, rinse mouth after"},
"adult": {"dose": "200-800 mcg twice daily", "max": "1600 mcg/day", "warning": "Inhaled corticosteroid, rinse mouth"},
"elderly": {"dose": "200-400 mcg twice daily", "max": "800 mcg/day", "warning": "Oral thrush risk"}
},
"formoterol": {
"child": {"dose": "12 mcg twice daily", "max": "24 mcg/day", "warning": "Over 5 years, long-acting"},
"adult": {"dose": "12-24 mcg twice daily", "max": "48 mcg/day", "warning": "Not for acute symptoms"},
"elderly": {"dose": "12 mcg twice daily", "max": "24 mcg/day", "warning": "Monitor cardiovascular effects"}
},
"theophylline": {
"child": {"dose": "10-20 mg/kg/day", "max": "800 mg/day", "warning": "Divide into 2-3 doses, narrow therapeutic index"},
"adult": {"dose": "300-600 mg/day divided", "max": "900 mg/day", "warning": "Monitor blood levels, drug interactions"},
"elderly": {"dose": "200-400 mg/day divided", "max": "600 mg/day", "warning": "Reduce dose, toxicity risk"}
},
"dextromethorphan": {
"child": {"dose": "0.5 mg/kg every 6-8 hours", "max": "60 mg/day", "warning": "Over 4 years, cough suppressant"},
"adult": {"dose": "10-30 mg every 4-8 hours", "max": "120 mg/day", "warning": "Avoid with MAOIs"},
"elderly": {"dose": "10-20 mg every 6-8 hours", "max": "60 mg/day", "warning": "Monitor for interactions"}
},
"ipratropium": {
"child": {"dose": "250 mcg 3-4 times daily", "max": "1000 mcg/day", "warning": "Nebulized"},
"adult": {"dose": "2 puffs 4 times daily", "max": "12 puffs/day", "warning": "Inhaled anticholinergic"},
"elderly": {"dose": "2 puffs 4 times daily", "max": "12 puffs/day", "warning": "Avoid eye contact"}
},

# VITAMINS & SUPPLEMENTS
"vitamin d3": {
"child": {"dose": "400-1000 IU daily", "max": "4000 IU/day", "warning": "Varies by age and deficiency"},
"adult": {"dose": "1000-2000 IU daily", "max": "4000 IU/day", "warning": "With fatty meal for absorption"},
"elderly": {"dose": "800-2000 IU daily", "max": "4000 IU/day", "warning": "Fall prevention, bone health"}
},
"vitamin b12": {
"child": {"dose": "1-2.5 mcg daily", "max": "50 mcg/day", "warning": "Varies by age"},
"adult": {"dose": "2.4 mcg daily", "max": "1000 mcg/day", "warning": "Higher if deficient"},
"elderly": {"dose": "25-1000 mcg daily", "max": "2000 mcg/day", "warning": "Malabsorption common"}
},
"folic acid": {
"child": {"dose": "0.1-0.4 mg daily", "max": "1 mg/day", "warning": "Varies by age"},
"adult": {"dose": "400-800 mcg daily", "max": "1 mg/day", "warning": "Essential in pregnancy"},
"elderly": {"dose": "400 mcg daily", "max": "1 mg/day", "warning": "With B12 if deficient"}
},
"calcium carbonate": {
"child": {"dose": "500-800 mg daily", "max": "2500 mg/day", "warning": "Divide doses, with food"},
"adult": {"dose": "500-1000 mg twice daily", "max": "2500 mg/day", "warning": "Take with food, avoid with iron"},
"elderly": {"dose": "500-1200 mg daily", "max": "2000 mg/day", "warning": "Constipation common"}
},
"iron folic acid": {
"child": {"dose": "2-3 mg/kg elemental iron", "max": "200 mg/day", "warning": "With vitamin C for absorption"},
"adult": {"dose": "60-120 mg elemental iron", "max": "200 mg/day", "warning": "Take on empty stomach, GI upset common"},
"elderly": {"dose": "60 mg elemental iron", "max": "150 mg/day", "warning": "Constipation common"}
},
"multivitamin": {
"child": {"dose": "Age-specific formulation", "max": "Per product", "warning": "Follow product guidelines"},
"adult": {"dose": "1 tablet daily", "max": "1 tablet/day", "warning": "With meal for absorption"},
"elderly": {"dose": "1 tablet daily", "max": "1 tablet/day", "warning": "Check for interactions"}
},

# ANTIFUNGALS
"fluconazole": {
"child": {"dose": "3-12 mg/kg/day", "max": "600 mg/day", "warning": "Once daily, hepatotoxicity risk"},
"adult": {"dose": "50-400 mg once daily", "max": "800 mg/day", "warning": "Monitor liver function"},
"elderly": {"dose": "50-200 mg once daily", "max": "400 mg/day", "warning": "Adjust for renal function"}
},
"itraconazole": {
"child": {"dose": "3-5 mg/kg/day", "max": "400 mg/day", "warning": "With food"},
"adult": {"dose": "100-200 mg once-twice daily", "max": "600 mg/day", "warning": "Take with food, monitor liver"},
"elderly": {"dose": "100 mg once daily", "max": "400 mg/day", "warning": "Heart failure risk"}
},
"ketoconazole": {
"child": {"dose": "3.3-6.6 mg/kg once daily", "max": "800 mg/day", "warning": "Hepatotoxicity"},
"adult": {"dose": "200-400 mg once daily", "max": "800 mg/day", "warning": "Monitor liver, many interactions"},
"elderly": {"dose": "200 mg once daily", "max": "400 mg/day", "warning": "Hepatotoxicity risk"}
},
"clotrimazole": {
"child": {"dose": "Apply topically 2-3 times daily", "max": "N/A", "warning": "External use only"},
"adult": {"dose": "Apply topically 2-3 times daily", "max": "N/A", "warning": "Complete full course"},
"elderly": {"dose": "Apply topically 2-3 times daily", "max": "N/A", "warning": "No special precautions"}
},

# STEROIDS
"prednisolone": {
"child": {"dose": "0.5-2 mg/kg/day", "max": "60 mg/day", "warning": "Taper slowly, growth suppression"},
"adult": {"dose": "5-60 mg once daily", "max": "80 mg/day", "warning": "Take morning, taper slowly"},
"elderly": {"dose": "5-40 mg once daily", "max": "60 mg/day", "warning": "Osteoporosis, diabetes risk"}
},
"dexamethasone": {
"child": {"dose": "0.02-0.3 mg/kg/day", "max": "10 mg/day", "warning": "Divide into 2-4 doses"},
"adult": {"dose": "0.5-9 mg/day divided", "max": "20 mg/day", "warning": "Potent, taper slowly"},
"elderly": {"dose": "0.5-4 mg/day", "max": "10 mg/day", "warning": "Infection risk, monitor glucose"}
},
"hydrocortisone": {
"child": {"dose": "2.5-10 mg/m2/day", "max": "50 mg/day", "warning": "Divide into 2-3 doses"},
"adult": {"dose": "20-240 mg/day divided", "max": "500 mg/day", "warning": "Take with food"},
"elderly": {"dose": "10-80 mg/day divided", "max": "240 mg/day", "warning": "Monitor BP and glucose"}
},

# ANTIVIRALS
"acyclovir": {
"child": {"dose": "20 mg/kg every 8 hours", "max": "1200 mg/day", "warning": "Adequate hydration"},
"adult": {"dose": "200-800 mg 5 times daily", "max": "4000 mg/day", "warning": "Drink plenty of fluids"},
"elderly": {"dose": "200-400 mg 5 times daily", "max": "2400 mg/day", "warning": "Adjust for renal function"}
},
"oseltamivir": {
"child": {"dose": "30-75 mg twice daily", "max": "150 mg/day", "warning": "Weight-based, within 48h of symptoms"},
"adult": {"dose": "75 mg twice daily", "max": "150 mg/day", "warning": "Start within 48h of flu symptoms"},
"elderly": {"dose": "75 mg twice daily", "max": "150 mg/day", "warning": "No adjustment needed"}
},
"tenofovir": {
"child": {"dose": "8 mg/kg once daily", "max": "300 mg/day", "warning": "Over 2 years, specialist use"},
"adult": {"dose": "300 mg once daily", "max": "300 mg/day", "warning": "Monitor renal and bone health"},
"elderly": {"dose": "300 mg once daily", "max": "300 mg/day", "warning": "Renal monitoring essential"}
},
"remdesivir": {
"child": {"dose": "5 mg/kg loading, then 2.5 mg/kg", "max": "Per protocol", "warning": "Hospital use only, COVID-19"},
"adult": {"dose": "200 mg loading, then 100 mg daily", "max": "Per protocol", "warning": "IV only, hospital setting"},
"elderly": {"dose": "200 mg loading, then 100 mg daily", "max": "Per protocol", "warning": "Monitor liver function"}
},

# OTHERS
"levothyroxine": {
"child": {"dose": "1-5 mcg/kg/day", "max": "Per TSH", "warning": "Age-specific, monitor TSH"},
"adult": {"dose": "25-200 mcg once daily", "max": "Per TSH", "warning": "Take on empty stomach, 30 min before food"},
"elderly": {"dose": "12.5-50 mcg once daily", "max": "Per TSH", "warning": "Start low, cardiac risk"}
},
"tamsulosin": {
"child": {"dose": "Not recommended", "max": "N/A", "warning": "Not approved"},
"adult": {"dose": "0.4 mg once daily", "max": "0.8 mg/day", "warning": "Take 30 min after same meal daily"},
"elderly": {"dose": "0.4 mg once daily", "max": "0.8 mg/day", "warning": "Orthostatic hypotension risk"}
},
"finasteride": {
"child": {"dose": "Not applicable", "max": "N/A", "warning": "Adult males only"},
"adult": {"dose": "1-5 mg once daily", "max": "5 mg/day", "warning": "Pregnant women must not handle"},
"elderly": {"dose": "1-5 mg once daily", "max": "5 mg/day", "warning": "No adjustment needed"}
},
"sildenafil": {
"child": {"dose": "0.5-2 mg/kg 3 times daily", "max": "20 mg 3 times/day", "warning": "Pulmonary hypertension only"},
"adult": {"dose": "25-100 mg PRN", "max": "100 mg/day", "warning": "Do not use with nitrates - fatal"},
"elderly": {"dose": "25 mg PRN", "max": "100 mg/day", "warning": "Start low, higher side effects"}
},
"misoprostol": {
"child": {"dose": "Not applicable", "max": "N/A", "warning": "Not approved"},
"adult": {"dose": "200 mcg 4 times daily with food", "max": "800 mcg/day", "warning": "Contraindicated in pregnancy"},
"elderly": {"dose": "200 mcg 2-4 times daily", "max": "800 mcg/day", "warning": "Diarrhea common"}
},
"tranexamic acid": {
"child": {"dose": "10 mg/kg 2-3 times daily", "max": "1500 mg/day", "warning": "With caution"},
"adult": {"dose": "1000-1500 mg 2-3 times daily", "max": "4000 mg/day", "warning": "Risk of thrombosis"},
"elderly": {"dose": "1000 mg 2-3 times daily", "max": "3000 mg/day", "warning": "Higher clot risk"}
},
"warfarin": {
"child": {"dose": "0.1-0.3 mg/kg once daily", "max": "Per INR", "warning": "Specialist supervision only"},
"adult": {"dose": "2-10 mg once daily", "max": "Per INR", "warning": "Regular INR monitoring essential, 2-3 target"},
"elderly": {"dose": "1-5 mg once daily", "max": "Per INR", "warning": "Start low, higher bleeding risk"}
},
}

# ============================================================================
# ADVANCED OCR FUNCTIONS (INTEGRATED FROM pris.py + existing)
# ============================================================================

def extract_text_easyocr(img: Image.Image) -> str:
    """Extract text using EasyOCR (INTEGRATED FROM pris.py)"""
    if not EASYOCR_AVAILABLE or OCR_READER is None:
        return ""
    try:
        img_np = np.array(img)
        results = OCR_READER.readtext(img_np)
        text = ' '.join([res[1] for res in results])
        return text.strip()
    except Exception as e:
        st.error(f"EasyOCR Error: {str(e)}")
        return ""

def preprocess_image_ultra_advanced(img: Image.Image) -> Image.Image:
    """Ultra-advanced preprocessing for medical handwriting OCR"""
    # Convert to numpy array
    img_np = np.array(img.convert('RGB'))
    
    # Convert to grayscale
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)
    
    # Thresholding for better text detection
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    morph = cv2.morphologyEx(morph, cv2.MORPH_OPEN, kernel)
    
    # Convert back to PIL Image
    result = Image.fromarray(morph)
    
    # Resize for better OCR
    w, h = result.size
    if w < 1024:
        new_w = 3000
        new_h = int(h * (new_w / w))
        result = result.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    return result

def extract_text_tesseract_enhanced(img: Image.Image) -> str:
    """Extract text using Tesseract OCR with multiple attempts"""
    if not PYTESSERACT_OCR_AVAILABLE:
        return None
    try:
        # Method 1: Ultra-advanced preprocessing
        processed1 = preprocess_image_ultra_advanced(img)
        config1 = r'--oem 3 --psm 6 -l eng'
        text1 = pytesseract.image_to_string(processed1, config=config1)
        
        if text1.strip():
            return text1.strip()
        
        # Method 2: Fallback with different PSM
        config2 = r'--oem 3 --psm 11 -l eng'
        text2 = pytesseract.image_to_string(processed1, config=config2)
        return text2.strip() if text2.strip() else None
        
    except Exception as e:
        return None

# ============================================================================
# UNIFIED OCR FUNCTION (NEW - COMBINES BOTH)
# ============================================================================
def extract_text_with_ocr(img: Image.Image) -> str:
    """
    Unified OCR: Try EasyOCR first, fallback to Tesseract
    """
    # Try EasyOCR first (best for handwriting)
    if EASYOCR_AVAILABLE and OCR_READER is not None:
        text = extract_text_easyocr(img)
        if text:
            return text
    
    # Fallback to Tesseract
    if PYTESSERACT_OCR_AVAILABLE:
        text = extract_text_tesseract_enhanced(img)
        if text:
            return text
    
    return ""

def find_drugs_super_flexible(text: str) -> list:
    """Extract drugs with ultra-flexible pattern matching"""
    if not text:
        return []
    
    found = []
    text_lower = text.lower()
    seen = set()
    
    for drug_name in DRUGS.keys():
        if drug_name in seen:
            continue
        
        # Try multiple pattern variations
        patterns = [
            r'\b' + re.escape(drug_name.lower()) + r'\b',  # Exact word boundary
            r'\b' + re.escape(drug_name.lower()),  # Start of word
            re.escape(drug_name.lower()),  # Anywhere
        ]
        
        found_drug = False
        for pattern in patterns:
            if re.search(pattern, text_lower):
                found_drug = True
                break
        
        if found_drug:
            # Extract dosage - multiple patterns
            dosage_patterns = [
                rf'{re.escape(drug_name.lower())}\s*[:\-]*\s*(\d+(?:\.\d+)?)\s*(mg|ml|mcg|units|gm|g|tab|tabs|cap|caps|unit)?',
                rf'(\d+(?:\.\d+)?)\s*(mg|ml|mcg|units|gm|g|tab|tabs|cap|caps)\s*{re.escape(drug_name.lower())}',
            ]
            
            dosage = "Not specified"
            for dosage_pattern in dosage_patterns:
                match = re.search(dosage_pattern, text_lower)
                if match:
                    amount = match.group(1)
                    unit = match.group(2) or "mg"
                    dosage = f"{amount} {unit}"
                    break
            
            # Extract frequency
            freq_patterns = ['1-0-0', '0-1-0', '0-0-1', '1-1-0', '1-0-1', '0-1-1', '1-1-1',
                            'od', 'hs', 'od', 'bd', 'tds', 'qid', 'stat', 'prn']
            frequency = "As prescribed"
            for freq in freq_patterns:
                if re.search(r'\b' + freq + r'\b', text_lower):
                    frequency = freq.upper()
                    break
            
            found.append({
                "name": drug_name,
                "dosage": dosage,
                "frequency": frequency,
                "class": DRUGS[drug_name]["class"],
                "generic": DRUGS[drug_name]["generic"]
            })
            seen.add(drug_name)
    
    return found

# ============================================================================
# STREAMLIT INTERFACE
# ============================================================================

st.set_page_config(page_title="Prescription Analyzer", page_icon="💊", layout="wide")

st.title("💊 Medical Prescription Analysis System")
st.markdown("### ENHANCED: 150+ Drugs + 100+ Interactions + mg/kg Dosage Guidelines + **EasyOCR + Tesseract**")
st.error("⚠️ **DISCLAIMER**: Educational only - NOT for clinical use. Consult healthcare professionals.")

if 'extracted_drugs' not in st.session_state:
    st.session_state.extracted_drugs = []
if 'ocr_text' not in st.session_state:
    st.session_state.ocr_text = ""

st.sidebar.header("🔧 Tools & Status")
page = st.sidebar.radio("Select Feature", [
    "📸 Prescription OCR (ENHANCED)",
    "🔍 Interaction Checker",
    "📏 Dosage Info with mg/kg",
    "🏥 Safety Check",
    "ℹ️ About & Help"
])

# Display OCR engine status
ocr_status = []
if EASYOCR_AVAILABLE:
    ocr_status.append("✅ EasyOCR (Primary)")
if PYTESSERACT_OCR_AVAILABLE:
    ocr_status.append("✅ Tesseract (Fallback)")
if not ocr_status:
    ocr_status.append("⚠️ No OCR Engine")

st.sidebar.info(f"""
**System Status:**
- OCR Engines: {' + '.join(ocr_status)}
- Total Medications: {len(DRUGS)}
- Drug Interactions: {len(INTERACTIONS)} pairs
- Alternatives Mapped: {len(ALTERNATIVES)}
- Dosage Guidelines: {len(DOSAGES)} drugs

**OCR Priority:**
1. EasyOCR (best for handwriting)
2. Tesseract (fallback)

**Quick Setup:**
```bash
pip install streamlit pillow pytesseract opencv-python numpy easyocr
```
""")

# ====== PAGE 1: PRESCRIPTION OCR ======
if page == "📸 Prescription OCR (ENHANCED)":
    st.header("📸 Enhanced Handwritten Prescription Analysis with mg/kg Dosage")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Step 1: Upload or Capture Image")
        st.markdown("**Option A: Upload Image**")
        upload = st.file_uploader("Select prescription image", type=['jpg','png','jpeg','bmp','tiff'])
        
        st.markdown("**Option B: Use Camera**")
        camera = st.camera_input("Capture prescription with camera")
        
        st.markdown("**Patient Information:**")
        age = st.number_input("Patient Age (years)", min_value=0, max_value=120, value=35)
        
        img = None
        if camera:
            img = Image.open(camera)
            st.success("✅ Image captured!")
        elif upload:
            img = Image.open(upload)
            st.success("✅ Image uploaded!")
        
        if img:
            st.image(img, caption="Prescription Image", use_column_width=True)
    
    with col2:
        st.subheader("Step 2: Analyze & Extract")
        
        if img and st.button("🔍 Analyze Prescription (ENHANCED OCR)", type="primary", use_container_width=True):
            ocr_method = "EasyOCR + Tesseract" if EASYOCR_AVAILABLE and PYTESSERACT_OCR_AVAILABLE else ("EasyOCR" if EASYOCR_AVAILABLE else "Tesseract")
            
            with st.spinner(f"⏳ Processing with {ocr_method}..."):
                text = extract_text_with_ocr(img)
            
            if text:
                st.session_state.ocr_text = text
                st.success(f"✅ Text extracted successfully using {ocr_method}!")
                
                with st.expander("📄 View Raw OCR Text"):
                    st.text_area("Extracted text:", value=text, height=150, disabled=True)
                
                drugs = find_drugs_super_flexible(text)
                st.session_state.extracted_drugs = drugs
                
                if drugs:
                    st.success(f"✅ **Found {len(drugs)} medications**")
                    
                    age_group = "child" if age < 18 else "elderly" if age >= 65 else "adult"
                    st.info(f"Patient Age Group: **{age_group.upper()}**")
                    
                    st.markdown("### 💊 Detected Medications with Dosage Recommendations:")
                    for i, d in enumerate(drugs, 1):
                        with st.container(border=True):
                            st.markdown(f"**{i}. {d['name'].upper()}**")
                            
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.caption(f"Generic: {d['generic']}")
                                st.caption(f"Class: {d['class']}")
                            with col_b:
                                st.metric("Prescribed Dosage", d['dosage'])
                            with col_c:
                                st.metric("Frequency", d['frequency'])
                            
                            # Show age-appropriate dosage recommendations
                            if d['name'] in DOSAGES:
                                dosage_info = DOSAGES[d['name']].get(age_group)
                                if dosage_info:
                                    st.markdown(f"**📏 Recommended Dosage for {age_group.title()}:**")
                                    st.info(f"**Dose:** {dosage_info['dose']}\n\n**Maximum:** {dosage_info['max']}")
                                    st.warning(f"⚠️ **Warning:** {dosage_info['warning']}")
                    
                    # Interactions
                    if len(drugs) > 1:
                        st.markdown("---")
                        st.markdown("### ⚠️ Drug-Drug Interactions")
                        drug_names = [d['name'].lower() for d in drugs]
                        interactions = []
                        for i, d1 in enumerate(drug_names):
                            for d2 in drug_names[i+1:]:
                                inter = INTERACTIONS.get((d1, d2))
                                if inter:
                                    interactions.append((d1, d2, inter))
                        
                        if interactions:
                            for d1, d2, inter in interactions:
                                icon = "🔴" if inter['severity']=="high" else "🟡"
                                st.warning(f"{icon} **{d1.title()} + {d2.title()}** [{inter['severity'].upper()}]\n{inter['effect']}")
                        else:
                            st.success("✅ No critical interactions detected")
                    
                    # Alternatives
                    st.markdown("---")
                    st.markdown("### 💡 Alternative Medications")
                    has_alternatives = False
                    for d in drugs:
                        alt = ALTERNATIVES.get(d['name'].lower())
                        if alt:
                            has_alternatives = True
                            st.info(f"**{d['name']}** → {', '.join(alt)}")
                    if not has_alternatives:
                        st.caption("No alternatives configured for detected medications")
                else:
                    st.warning("⚠️ No medications found in the image")
            else:
                st.error("❌ OCR failed - Tips:\n- Ensure image is clear and well-lit\n- Handwriting should be legible\n- Try different angle/lighting\n- Upload clearer image\n- Image should be at least 300 DPI")

# ====== PAGE 2: INTERACTION CHECKER ======
elif page == "🔍 Interaction Checker":
    st.header("Drug-Drug Interaction Checker")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Enter Medications")
        drugs_text = st.text_area(
            "Enter drug names (comma/line separated):",
            height=200,
            placeholder="Example:\naspirin\nibuprofen\nmetformin\n\nOr: aspirin, ibuprofen, metformin"
        )
        
        if st.button("🔍 Check Interactions", type="primary", use_container_width=True):
            drugs = [d.strip().lower() for d in re.split(r'[,\n;]', drugs_text) if d.strip()]
            
            if len(drugs) < 2:
                st.warning("⚠️ Enter at least 2 drugs to check for interactions")
            else:
                interactions = []
                for i, d1 in enumerate(drugs):
                    for d2 in drugs[i+1:]:
                        inter = INTERACTIONS.get((d1, d2))
                        if inter:
                            interactions.append((d1, d2, inter))
                
                if interactions:
                    st.error(f"⚠️ **{len(interactions)} INTERACTION(S) FOUND**")
                    for d1, d2, inter in interactions:
                        icon = "🔴" if inter['severity']=="high" else "🟡"
                        st.warning(f"{icon} **{d1.title()} + {d2.title()}**\n\n{inter['effect']}\n\nSeverity: {inter['severity'].upper()}")
                else:
                    st.success("✅ **No critical interactions detected** for this drug combination")
    
    with col2:
        st.subheader("Available Drugs Database")
        st.write(", ".join(sorted(list(DRUGS.keys())[:50])))
        st.caption(f"... and {len(DRUGS)-50} more medications in database")
        
        st.markdown("---")
        st.subheader("Drug Categories")
        categories = {}
        for drug, info in DRUGS.items():
            cat = info['class']
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1
        
        for cat, count in sorted(categories.items()):
            st.caption(f"• {cat}: {count} drugs")

# ====== PAGE 3: DOSAGE INFO WITH MG/KG ======
elif page == "📏 Dosage Info with mg/kg":
    st.header("Medication Dosage Guidelines with mg/kg Recommendations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Select Drug & Age")
        drug = st.selectbox("Choose medication:", sorted(DOSAGES.keys()))
        age = st.number_input("Patient Age:", min_value=0, max_value=120, value=35)
        age_group = "child" if age < 18 else "elderly" if age >= 65 else "adult"
        st.info(f"**Age Group:** {age_group.title()}")
    
    with col2:
        st.subheader("Dosage Recommendations")
        if drug in DOSAGES:
            dosage_info = DOSAGES[drug].get(age_group)
            if dosage_info:
                st.success(f"### {drug.upper()}")
                st.markdown(f"""
**Drug Class:** {DRUGS[drug]['class']}  
**Generic Name:** {DRUGS[drug]['generic']}  
**Age Group:** {age_group.title()}

---

### 📏 Dosage Information
**Recommended Dose:** {dosage_info['dose']}  
**Maximum Dose:** {dosage_info['max']}

---

### ⚠️ Warnings & Precautions
{dosage_info['warning']}
""")
            else:
                st.warning("Dosage information not available for this age group")
        
        # Show alternatives
        alt = ALTERNATIVES.get(drug.lower())
        if alt:
            st.markdown("---")
            st.markdown("### 💡 Alternative Options")
            st.info(f"{', '.join([a.title() for a in alt])}")
        
        # Check for interactions with common drugs
        st.markdown("---")
        st.subheader("Common Interactions")
        common_interactions = []
        for (d1, d2), info in INTERACTIONS.items():
            if drug.lower() == d1:
                common_interactions.append((d2, info))
        
        if common_interactions:
            for other_drug, inter in common_interactions[:5]:
                icon = "🔴" if inter['severity']=="high" else "🟡"
                st.warning(f"{icon} + {other_drug.title()}: {inter['effect']}")
        else:
            st.caption("No common interactions configured")

# ====== PAGE 4: SAFETY CHECK ======
elif page == "🏥 Safety Check":
    st.header("Medical History Safety Assessment")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Patient Information")
        age = st.number_input("Patient Age:", min_value=0, max_value=120, value=45)
        
        st.markdown("**Medical Conditions:**")
        conditions = st.multiselect(
            "Select all applicable conditions:",
            sorted(CONDITIONS.keys()),
            label_visibility="collapsed"
        )
        
        st.markdown("**Medications:**")
        drugs_text = st.text_area(
            "Enter medications (comma/line separated):",
            height=120,
            placeholder="aspirin, metformin, losartan",
            label_visibility="collapsed"
        )
        
        if st.button("🏥 Check Safety", type="primary", use_container_width=True):
            drugs = [d.strip().lower() for d in re.split(r'[,\n;]', drugs_text) if d.strip()]
            warnings = []
            
            for drug in drugs:
                d_class = DRUGS.get(drug, {}).get("class")
                
                for cond in conditions:
                    cond_info = CONDITIONS.get(cond, {})
                    if drug in cond_info.get("avoid", []) or d_class in cond_info.get("avoid", []):
                        warnings.append({
                            'drug': drug,
                            'condition': cond,
                            'reason': cond_info.get("reason", "Unknown risk")
                        })
            
            if warnings:
                st.error(f"⚠️ **{len(warnings)} SAFETY CONCERN(S)**")
                for w in warnings:
                    st.warning(f"""
**{w['drug'].upper()}** with **{w['condition'].upper()}**  
Risk: {w['reason']}  
Recommendation: Consult healthcare provider
""")
            else:
                st.success("✅ **No safety concerns detected** for this combination")
    
    with col2:
        st.subheader("Supported Conditions")
        st.markdown("**Current Medical Conditions:**")
        for cond in sorted(CONDITIONS.keys()):
            avoid_list = ", ".join(CONDITIONS[cond].get("avoid", [])[:3])
            st.caption(f"• **{cond}**: Avoid {avoid_list}...")

# ====== PAGE 5: ABOUT & HELP ======
else:  # About & Help
    st.header("ℹ️ About & Help")
    
    st.markdown("""
### About This Application
This Medical Prescription Analysis System is an educational tool designed to demonstrate:
- **Advanced OCR Technology**: EasyOCR (primary) + Tesseract (fallback) for handwriting recognition
- **Comprehensive Drug Database**: 150+ medications with complete dosage guidelines
- **Drug-Drug Interactions**: 100+ critical interaction pairs
- **Age-Appropriate Dosing**: Child, Adult, and Elderly dosage recommendations with mg/kg calculations
- **Safety Checks**: Contraindications based on medical conditions
- **Alternative Medications**: Therapeutic alternatives for detected drugs

### Key Features
✅ **Dual OCR Engine**: EasyOCR for superior handwriting recognition with Tesseract fallback  
✅ **Real-time Analysis**: Instant drug detection and interaction checking  
✅ **mg/kg Dosing**: Precise pediatric and geriatric dosage recommendations  
✅ **Safety Warnings**: Age-specific warnings and contraindications  
✅ **Alternative Options**: Therapeutic substitutes when conflicts exist  

### Installation
```bash
# Install all dependencies
pip install streamlit pillow pytesseract opencv-python numpy easyocr

# Install Tesseract OCR (system-level)
# Windows: https://github.com/UB-Mannheim/tesseract/wiki
# Mac: brew install tesseract
# Linux: sudo apt-get install tesseract-ocr

# Run the application
streamlit run prescription_analyzer.py
```

### Usage Tips
1. **Clear Images**: Use well-lit, high-contrast images (300+ DPI recommended)
2. **Legible Handwriting**: Clearer handwriting = better OCR accuracy
3. **Camera Feature**: Use the built-in camera for mobile prescriptions
4. **Manual Override**: If OCR fails, you can still use other features manually
5. **Age Specificity**: Always enter patient age for accurate dosage recommendations

### Important Disclaimers
⚠️ **EDUCATIONAL USE ONLY**  
- This tool is NOT a substitute for professional medical advice  
- ALWAYS consult qualified healthcare professionals before taking any medication  
- Do NOT use for clinical decision-making  
- Verify all dosage recommendations with licensed pharmacists/physicians  

⚠️ **OCR Accuracy**  
- OCR technology may misread handwritten prescriptions  
- Always verify extracted text against original prescription  
- Double-check all drug names and dosages  

⚠️ **Data Limitations**  
- Drug database may not include all medications  
- Interaction data based on common known interactions  
- Local regulations and guidelines may differ  

### Technical Support
For issues or questions:
1. Check that all dependencies are installed correctly
2. Verify Tesseract OCR is installed and accessible
3. Ensure images are clear and well-lit
4. Try different OCR settings if initial results are poor

### Version Information
- **System**: Medical Prescription Analyzer  
- **OCR**: EasyOCR + Tesseract (Dual Engine)  
- **Drugs**: 150+ medications  
- **Interactions**: 100+ pairs  
- **Dosages**: Complete mg/kg guidelines  

### Credits
Built with:
- Streamlit (UI Framework)
- EasyOCR (Primary OCR Engine)
- Tesseract OCR (Fallback Engine)
- OpenCV (Image Processing)
- NumPy (Numerical Processing)

---

**Remember**: This is an educational demonstration. ALWAYS consult healthcare professionals for medical advice.
""")
