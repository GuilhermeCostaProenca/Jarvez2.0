"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Ability_1 = require("../../Ability");
const Character_1 = require("../../Character");
const Sheet_1 = require("../../Sheet");
const Transaction_1 = require("../../Sheet/Transaction");
const SkillName_1 = require("../../Skill/SkillName");
const RoleAbilityName_1 = require("../RoleAbilityName");
const Knight_1 = require("./Knight");
describe('Knight', () => {
    let knight;
    let sheet;
    let transaction;
    let character;
    beforeEach(() => {
        sheet = new Sheet_1.BuildingSheet();
        transaction = new Transaction_1.Transaction(sheet);
        knight = new Knight_1.Knight([
            [
                SkillName_1.SkillName.animalHandling,
                SkillName_1.SkillName.athletics,
            ],
        ]);
        knight.addToSheet(transaction);
        character = new Character_1.Character(sheet);
    });
    it('should have honour code ability', () => {
        const roleAbilities = sheet.getSheetAbilities().getRoleAbilities();
        expect(roleAbilities.get(RoleAbilityName_1.RoleAbilityName.honourCode)).toBeDefined();
    });
    it('should have bulwark ability', () => {
        const roleAbilities = sheet.getSheetAbilities().getRoleAbilities();
        expect(roleAbilities.get(RoleAbilityName_1.RoleAbilityName.bulwark)).toBeDefined();
    });
    it('should have bulwark defense triggered effect', () => {
        const effects = sheet.getSheetTriggeredEffects();
        const defenseEffects = effects.getByEvent(Ability_1.TriggerEvent.defend);
        expect(defenseEffects).toHaveLength(1);
        expect(defenseEffects.get(Ability_1.TriggeredEffectName.bulwark)).toBeDefined();
    });
    it('should have bulwark resistance test triggered effect', () => {
        const effects = sheet.getSheetTriggeredEffects();
        const resistanceEffects = effects.getByEvent(Ability_1.TriggerEvent.resistanceTest);
        expect(resistanceEffects).toHaveLength(1);
    });
    it('should enable bulwark receiving +2 defense', () => {
        var _a;
        const effects = character.getDefenseTriggeredEffects();
        const effect = effects.get(Ability_1.TriggeredEffectName.bulwark);
        effect === null || effect === void 0 ? void 0 : effect.enable({
            effectName: Ability_1.TriggeredEffectName.bulwark,
        });
        expect(character.modifiers.defense.fixed.get(RoleAbilityName_1.RoleAbilityName.bulwark)).toBeDefined();
        expect((_a = character.modifiers.defense.fixed.get(RoleAbilityName_1.RoleAbilityName.bulwark)) === null || _a === void 0 ? void 0 : _a.baseValue).toBe(2);
    });
    it('should disable bulwark receiving +2 defense', () => {
        const effects = character.getDefenseTriggeredEffects();
        const effect = effects.get(Ability_1.TriggeredEffectName.bulwark);
        effect === null || effect === void 0 ? void 0 : effect.enable({
            effectName: Ability_1.TriggeredEffectName.bulwark,
        });
        effect === null || effect === void 0 ? void 0 : effect.disable();
        expect(character.modifiers.defense.fixed.get(RoleAbilityName_1.RoleAbilityName.bulwark)).toBeUndefined();
    });
});
