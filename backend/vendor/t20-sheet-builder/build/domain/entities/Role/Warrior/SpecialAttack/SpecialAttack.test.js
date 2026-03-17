"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Ability_1 = require("../../../Ability");
const Character_1 = require("../../../Character");
const Inventory_1 = require("../../../Inventory");
const Origin_1 = require("../../../Origin");
const Power_1 = require("../../../Power");
const Race_1 = require("../../../Race");
const SheetBuilder_1 = require("../../../Sheet/SheetBuilder");
const Skill_1 = require("../../../Skill");
const RoleAbilityName_1 = require("../../RoleAbilityName");
const Warrior_1 = require("../Warrior");
describe('SpecialAttack', () => {
    let sheet;
    let role;
    let race;
    let sheetBuilder;
    let origin;
    let character;
    let context;
    beforeEach(() => {
        const choices = [
            new Race_1.VersatileChoiceSkill(Skill_1.SkillName.acrobatics),
            new Race_1.VersatileChoicePower(new Power_1.OneWeaponStyle()),
        ];
        race = new Race_1.Human(['charisma', 'constitution', 'dexterity'], choices);
        role = new Warrior_1.Warrior([[Skill_1.SkillName.fight], [Skill_1.SkillName.aim, Skill_1.SkillName.athletics]]);
        sheetBuilder = new SheetBuilder_1.SheetBuilder();
        origin = new Origin_1.Acolyte([new Origin_1.OriginBenefitGeneralPower(new Power_1.IronWill()), new Origin_1.OriginBenefitSkill(Skill_1.SkillName.cure)]);
        sheet = sheetBuilder
            .setInitialAttributes({ strength: 2, dexterity: 0, charisma: 0, constitution: 0, intelligence: 0, wisdom: 2 })
            .chooseRace(race)
            .chooseRole(role)
            .chooseOrigin(origin)
            .trainIntelligenceSkills([])
            .addInitialEquipment({
            simpleWeapon: new Inventory_1.Dagger(),
            armor: new Inventory_1.LeatherArmor(),
            martialWeapon: new Inventory_1.LongSword(),
            money: 24,
        })
            .build();
        character = new Character_1.Character(sheet);
    });
    let dagger;
    beforeEach(() => {
        const attacks = character.getAttacks();
        dagger = attacks.get(Inventory_1.EquipmentName.dagger);
    });
    it('should enable special attack', () => {
        const attack = character.getAttacks().get(Inventory_1.EquipmentName.dagger);
        attack.enableTriggeredEffect({
            effectName: Ability_1.TriggeredEffectName.specialAttack,
            bonus: 'attack',
        });
        const modifier = attack.modifiers.test.fixed.get(RoleAbilityName_1.RoleAbilityName.specialAttack);
        expect(modifier).toBeDefined();
        expect(modifier === null || modifier === void 0 ? void 0 : modifier.baseValue).toBe(4);
    });
    it('should enable special attack splitting bonus', () => {
        const attack = character.getAttacks().get(Inventory_1.EquipmentName.dagger);
        attack.enableTriggeredEffect({
            effectName: Ability_1.TriggeredEffectName.specialAttack,
            bonus: 'both',
        });
        const modifier = attack.modifiers.test.fixed.get(RoleAbilityName_1.RoleAbilityName.specialAttack);
        expect(modifier).toBeDefined();
        expect(modifier === null || modifier === void 0 ? void 0 : modifier.baseValue).toBe(2);
        const damageModifier = attack.modifiers.damage.fixed.get(RoleAbilityName_1.RoleAbilityName.specialAttack);
        expect(damageModifier).toBeDefined();
        expect(damageModifier === null || damageModifier === void 0 ? void 0 : damageModifier.baseValue).toBe(2);
    });
    it('should enable special attack on damage', () => {
        const attack = character.getAttacks().get(Inventory_1.EquipmentName.dagger);
        attack.enableTriggeredEffect({
            effectName: Ability_1.TriggeredEffectName.specialAttack,
            bonus: 'damage',
        });
        const modifier = attack.modifiers.damage.fixed.get(RoleAbilityName_1.RoleAbilityName.specialAttack);
        expect(modifier).toBeDefined();
        expect(modifier === null || modifier === void 0 ? void 0 : modifier.baseValue).toBe(4);
    });
    it('should enable special attack using 2 mana points', () => {
        const attack = character.getAttacks().get(Inventory_1.EquipmentName.dagger);
        attack.enableTriggeredEffect({
            effectName: Ability_1.TriggeredEffectName.specialAttack,
            mana: 2,
        });
        const manaCost = attack.getManaCost();
        expect(manaCost).toBeDefined();
        expect(manaCost === null || manaCost === void 0 ? void 0 : manaCost.value).toBe(2);
        const modifier = attack.modifiers.test.fixed.get(RoleAbilityName_1.RoleAbilityName.specialAttack);
        expect(modifier).toBeDefined();
        expect(modifier === null || modifier === void 0 ? void 0 : modifier.baseValue).toBe(8);
    });
});
