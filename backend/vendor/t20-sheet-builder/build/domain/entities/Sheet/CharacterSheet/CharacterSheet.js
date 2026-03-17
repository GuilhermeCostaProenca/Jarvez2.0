"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CharacterSheet = void 0;
const Sheet_1 = require("../Sheet");
const CharacterSheetOrigin_1 = require("./CharacterSheetOrigin");
const CharacterSheetRace_1 = require("./CharacterSheetRace");
const CharacterSheetRole_1 = require("./CharacterSheetRole");
class CharacterSheet extends Sheet_1.Sheet {
    constructor(params) {
        super();
        this.sheetRace = new CharacterSheetRace_1.CharacterSheetRace(params.race);
        this.sheetRole = new CharacterSheetRole_1.CharacterSheetRole(params.role);
        this.sheetOrigin = new CharacterSheetOrigin_1.CharacterSheetOrigin(params.origin);
        this.sheetSkills = params.skills;
        this.sheetAttributes = params.attributes;
        this.sheetLifePoints = params.lifePoints;
        this.sheetManaPoints = params.manaPoints;
        this.level = params.level;
        this.sheetVision = params.vision;
        this.sheetDisplacement = params.displacement;
        this.sheetDefense = params.defense;
        this.buildSteps = params.buildSteps;
        this.sheetProficiencies = params.proficiencies;
        this.sheetAbilities = params.abilities;
        this.sheetPowers = params.powers;
        this.sheetSpells = params.spells;
        this.sheetInventory = params.inventory;
        this.sheetSize = params.size;
        this.sheetDevotion = params.devotion;
        this.sheetResistences = params.sheetResistences;
        this.sheetTriggeredEffects = params.sheetTriggeredEffects;
        this.activateableEffects = params.activateableEffects;
    }
}
exports.CharacterSheet = CharacterSheet;
