"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BuildingSheet = void 0;
const LifePoints_1 = require("../../Points/LifePoints/LifePoints");
const ManaPoints_1 = require("../../Points/ManaPoints/ManaPoints");
const Level_1 = require("../Level");
const Sheet_1 = require("../Sheet");
const SheetAbilities_1 = require("../SheetAbilities");
const SheetActivateableEffects_1 = require("../SheetActivateableEffects");
const SheetAttributes_1 = require("../SheetAttributes");
const SheetDefense_1 = require("../SheetDefense");
const SheetDevotion_1 = require("../SheetDevotion");
const SheetDisplacement_1 = require("../SheetDisplacement");
const SheetInventory_1 = require("../SheetInventory");
const SheetPoints_1 = require("../SheetPoints");
const SheetPowers_1 = require("../SheetPowers");
const SheetProficiencies_1 = require("../SheetProficiencies");
const SheetResistencies_1 = require("../SheetResistencies");
const SheetSize_1 = require("../SheetSize");
const SheetSkills_1 = require("../SheetSkills");
const SheetSpells_1 = require("../SheetSpells");
const SheetTriggeredEffects_1 = require("../SheetTriggeredEffects");
const SheetVision_1 = require("../SheetVision");
const BuildingSheetOrigin_1 = require("./BuildingSheetOrigin");
const BuildingSheetRace_1 = require("./BuildingSheetRace");
const BuildingSheetRole_1 = require("./BuildingSheetRole");
class BuildingSheet extends Sheet_1.Sheet {
    constructor() {
        super(...arguments);
        this.sheetRace = new BuildingSheetRace_1.BuildingSheetRace();
        this.sheetRole = new BuildingSheetRole_1.BuildingSheetRole();
        this.sheetOrigin = new BuildingSheetOrigin_1.BuildingSheetOrigin();
        this.sheetAbilities = new SheetAbilities_1.SheetAbilities();
        this.sheetLifePoints = new SheetPoints_1.SheetPoints(new LifePoints_1.LifePoints());
        this.sheetManaPoints = new SheetPoints_1.SheetPoints(new ManaPoints_1.ManaPoints());
        this.sheetSkills = new SheetSkills_1.SheetSkills();
        this.sheetAttributes = new SheetAttributes_1.SheetAttributes();
        this.sheetSpells = new SheetSpells_1.SheetSpells();
        this.sheetInventory = new SheetInventory_1.SheetInventory();
        this.sheetPowers = new SheetPowers_1.SheetPowers();
        this.sheetDefense = new SheetDefense_1.SheetDefense();
        this.sheetVision = new SheetVision_1.SheetVision();
        this.sheetProficiencies = new SheetProficiencies_1.SheetProficiencies();
        this.sheetDisplacement = new SheetDisplacement_1.SheetDisplacement();
        this.sheetDevotion = new SheetDevotion_1.SheetDevotion();
        this.sheetSize = new SheetSize_1.SheetSize();
        this.sheetResistences = new SheetResistencies_1.SheetResistences();
        this.buildSteps = [];
        this.level = Level_1.Level.one;
        this.sheetTriggeredEffects = new SheetTriggeredEffects_1.SheetTriggeredEffects();
        this.activateableEffects = new SheetActivateableEffects_1.SheetActivateableEffects();
    }
    getSheetRace() {
        return this.sheetRace;
    }
    getSheetRole() {
        return this.sheetRole;
    }
    getSheetOrigin() {
        return this.sheetOrigin;
    }
}
exports.BuildingSheet = BuildingSheet;
