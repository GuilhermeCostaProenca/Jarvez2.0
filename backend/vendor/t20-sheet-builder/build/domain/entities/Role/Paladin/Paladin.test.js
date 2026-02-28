"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Ability_1 = require("../../Ability");
const Character_1 = require("../../Character");
const Inventory_1 = require("../../Inventory");
const Sheet_1 = require("../../Sheet");
const SheetBuilder_1 = require("../../Sheet/SheetBuilder");
const Skill_1 = require("../../Skill");
const RoleAbilityName_1 = require("../RoleAbilityName");
const Paladin_1 = require("./Paladin");
describe('Paladin', () => {
    let sheet;
    let character;
    beforeEach(() => {
        const paladin = new Paladin_1.Paladin([[Skill_1.SkillName.animalHandling, Skill_1.SkillName.athletics]]);
        const builder = new SheetBuilder_1.SheetBuilder();
        builder
            .chooseRole(paladin)
            .addInitialEquipment({
            simpleWeapon: new Inventory_1.Dagger(),
            armor: new Inventory_1.LeatherArmor(),
            martialWeapon: new Inventory_1.LongSword(),
            money: 24,
        });
        sheet = builder.getBuildingSheet();
        character = new Character_1.Character(sheet);
    });
    it('should have blessed', () => {
        const blessed = sheet.getSheetAbilities()
            .getRoleAbilities()
            .get(RoleAbilityName_1.RoleAbilityName.blessed);
        expect(blessed).toBeDefined();
    });
    it('should have hero code', () => {
        const heroCode = sheet.getSheetAbilities()
            .getRoleAbilities()
            .get(RoleAbilityName_1.RoleAbilityName.heroCode);
        expect(heroCode).toBeDefined();
    });
    it('should have divine blow', () => {
        const divineBlow = sheet.getSheetAbilities()
            .getRoleAbilities()
            .get(RoleAbilityName_1.RoleAbilityName.divineBlow);
        expect(divineBlow).toBeDefined();
    });
    it('should add charisma to mana points', () => {
        sheet.getSheetAttributes().increaseAttribute('charisma', 2);
        const mana = sheet.getSheetManaPoints().getMax(sheet.getSheetAttributes().getValues(), Sheet_1.Level.one);
        expect(mana).toBe(5);
    });
    it('should have 2 granted powers', () => {
        const count = sheet.getSheetDevotion().getGrantedPowerCount();
        expect(count).toBe(2);
    });
    it('should have divine blow triggered effect', () => {
        const attack = character.getAttack(Inventory_1.EquipmentName.dagger);
        expect(attack).toBeDefined();
        expect(attack === null || attack === void 0 ? void 0 : attack.getTriggeredEffects().get(Ability_1.TriggeredEffectName.divineBlow)).toBeDefined();
    });
    it('should sum charisma to attack roll', () => {
        const sheetAttributes = sheet.getSheetAttributes();
        sheetAttributes.increaseAttribute('charisma', 2);
        const attack = character.getAttack(Inventory_1.EquipmentName.dagger);
        attack.enableTriggeredEffect({ effectName: Ability_1.TriggeredEffectName.divineBlow });
        const modifier = attack.modifiers.test.fixed.get(RoleAbilityName_1.RoleAbilityName.divineBlow);
        expect(modifier).toBeDefined();
        expect(modifier === null || modifier === void 0 ? void 0 : modifier.getTotalAttributeBonuses(sheetAttributes.getValues())).toBe(2);
    });
});
