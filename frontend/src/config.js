/**
 * LEAFSIGHT Frontend Configuration
 * Centralized API configuration point.
 */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export const DISEASE_INFO = {
  Bacterialblight: {
    displayName: "Bacterial Blight",
    pathogen: "Xanthomonas oryzae pv. oryzae",
    symptoms: "Water-soaked streaks on leaf blades that enlarge and turn yellowish-white with wavy margins.",
    management: "Use resistant cultivars, balanced nitrogen fertilization, and ensure field drainage.",
    severity: "High",
    color: "#e11d48", // Crimson rose
    bgColor: "#ffe4e6"
  },
  Blast: {
    displayName: "Rice Blast",
    pathogen: "Magnaporthe oryzae (Pyricularia oryzae)",
    symptoms: "Spindle-shaped or diamond-shaped lesions with grayish centers and dark brown borders on leaves.",
    management: "Apply recommended fungicides (e.g. Tricyclazole), avoid excess nitrogen, maintain continuous flood.",
    severity: "Critical",
    color: "#ea580c", // Amber orange
    bgColor: "#ffedd5"
  },
  Brownspot: {
    displayName: "Brown Spot",
    pathogen: "Bipolaris oryzae (Cochliobolus miyabeanus)",
    symptoms: "Circular to oval brown lesions with yellow halos distributed across the leaf blade.",
    management: "Improve soil fertility (potassium & micronutrients), treat seeds before sowing, manage water levels.",
    severity: "Moderate",
    color: "#d97706", // Ochre amber
    bgColor: "#fef3c7"
  },
  Tungro: {
    displayName: "Rice Tungro Disease",
    pathogen: "Rice tungro bacilliform virus & spherical virus (vectored by Green Leafhopper)",
    symptoms: "Stunted growth, reduced tillering, and yellow-orange discoloration starting from leaf tips.",
    management: "Control green leafhopper vectors, practice synchronous planting, rogue infected stubble.",
    severity: "Severe",
    color: "#9333ea", // Purple
    bgColor: "#f3e8ff"
  }
};

export const MODEL_BENCHMARKS = {
  accuracy: "99.86%",
  macroF1: "99.85%",
  macroPrecision: "99.83%",
  macroRecall: "99.88%",
  correctPredictions: "720 / 721",
  datasetSplit: "70% Train / 15% Val / 15% Test",
  architecture: "ViT-B/16 + GRU Classifier"
};
