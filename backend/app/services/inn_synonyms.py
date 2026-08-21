"""INN / BAN to USAN name mapping, plus salt-form equivalence.

US registries (Orange Book, openFDA) index drugs under USAN names, while a
brand team in India types the INN or the British name. "Paracetamol" finds
nothing in the Orange Book because it is filed as "acetaminophen", and
"clavulanic acid" misses because it is listed as "clavulanate potassium".
Without this layer those searches come back empty and look like missing data.
"""
from typing import List

# INN / BAN / common regional name -> the name US registries file under.
INN_TO_USAN = {
    "paracetamol": "acetaminophen",
    "salbutamol": "albuterol",
    "adrenaline": "epinephrine",
    "noradrenaline": "norepinephrine",
    "lignocaine": "lidocaine",
    "lignocaine hydrochloride": "lidocaine",
    "frusemide": "furosemide",
    "rifampicin": "rifampin",
    "amoxycillin": "amoxicillin",
    "clavulanic acid": "clavulanate",
    "potassium clavulanate": "clavulanate",
    "glibenclamide": "glyburide",
    "thyroxine": "levothyroxine",
    "pethidine": "meperidine",
    "indometacin": "indomethacin",
    "oestradiol": "estradiol",
    "oestrogen": "estrogen",
    "ciclosporin": "cyclosporine",
    "cyclosporin": "cyclosporine",
    "dothiepin": "dosulepin",
    "phenobarbitone": "phenobarbital",
    "hyoscine": "scopolamine",
    "trimethoprim and sulphamethoxazole": "sulfamethoxazole",
    "cotrimoxazole": "sulfamethoxazole",
    "co-trimoxazole": "sulfamethoxazole",
    "sulphasalazine": "sulfasalazine",
    "sulphamethoxazole": "sulfamethoxazole",
    "cephalexin": "cefalexin",
    "cephradine": "cefradine",
    "cefuroxime axetil": "cefuroxime",
    "beclomethasone": "beclometasone",
    "budesonide": "budesonide",
    "chlorpheniramine": "chlorphenamine",
    "dicyclomine": "dicycloverine",
    "metamizole": "dipyrone",
    "nifedipine": "nifedipine",
    "isoprenaline": "isoproterenol",
    "methylthioninium chloride": "methylene blue",
    "pentaerythritol tetranitrate": "pentaerithrityl tetranitrate",
    "sodium valproate": "valproate",
    "valproic acid": "valproate",
    "vitamin c": "ascorbic acid",
    "vitamin b1": "thiamine",
    "vitamin b6": "pyridoxine",
    "vitamin b12": "cyanocobalamin",
    "vitamin d3": "cholecalciferol",
}

# Reverse direction, so a US name still resolves when a source uses the INN.
USAN_TO_INN = {v: k for k, v in INN_TO_USAN.items()}

# Salt and ester suffixes that registries append to the base moiety.
_SALT_SUFFIXES = (
    "hydrochloride", "hcl", "sodium", "potassium", "calcium", "magnesium",
    "sulfate", "sulphate", "phosphate", "maleate", "tartrate", "besylate",
    "mesylate", "fumarate", "succinate", "acetate", "citrate", "nitrate",
    "bromide", "chloride", "carbonate", "gluconate", "lactate", "oxalate",
    "trihydrate", "dihydrate", "monohydrate", "anhydrous", "micronised",
    "micronized", "axetil", "proxetil", "dipropionate", "furoate", "valerate",
)


def base_moiety(name: str) -> str:
    """Strip trailing salt/ester words to get the active moiety."""
    words = name.strip().lower().split()
    while words and words[-1] in _SALT_SUFFIXES:
        words.pop()
    return " ".join(words) or name.strip().lower()


def candidates(name: str) -> List[str]:
    """Every spelling worth trying against a US drug registry, best first."""
    original = name.strip().lower()
    if not original:
        return []

    out: List[str] = [original]

    def add(value: str) -> None:
        value = value.strip().lower()
        if value and value not in out:
            out.append(value)

    add(INN_TO_USAN.get(original, ""))
    add(USAN_TO_INN.get(original, ""))

    moiety = base_moiety(original)
    add(moiety)
    add(INN_TO_USAN.get(moiety, ""))
    add(USAN_TO_INN.get(moiety, ""))

    # British "-ph-"/"-oe-" spellings that have no dedicated map entry.
    for variant in (original.replace("ph", "f"), original.replace("oe", "e"), original.replace("ae", "e")):
        if variant != original:
            add(variant)
            add(INN_TO_USAN.get(variant, ""))

    return out
