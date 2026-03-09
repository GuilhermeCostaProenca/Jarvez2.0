"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Ability_1 = require("../Ability");
const Attack_1 = require("../Attack");
const Inventory_1 = require("../Inventory");
const Origin_1 = require("../Origin");
const Power_1 = require("../Power");
const Race_1 = require("../Race");
const Role_1 = require("../Role");
const SheetBuilder_1 = require("../Sheet/SheetBuilder");
const Skill_1 = require("../Skill");
const Character_1 = require("./Character");
describe('Attack', () => {
    let sheet;
    let role;
    let race;
    let sheetBuilder;
    let origin;
    let character;
    beforeEach(() => {
        const choices = [
            new Race_1.VersatileChoiceSkill(Skill_1.SkillName.acrobatics),
            new Race_1.VersatileChoicePower(new Power_1.OneWeaponStyle()),
        ];
        race = new Race_1.Human(['charisma', 'constitution', 'dexterity'], choices);
        role = new Role_1.Warrior([[Skill_1.SkillName.fight], [Skill_1.SkillName.aim, Skill_1.SkillName.athletics]]);
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
        character.toggleEquipItem(Inventory_1.EquipmentName.lightShield);
    });
    let dagger;
    beforeEach(() => {
        const attacks = character.getAttacks();
        dagger = attacks.get(Inventory_1.EquipmentName.dagger);
    });
    it('should find dagger attack', () => {
        expect(dagger).toBeDefined();
        expect(dagger.attack).toEqual(new Attack_1.WeaponAttack(new Inventory_1.Dagger()));
    });
    it('should roll dagger attack', () => {
        const fakeRandom = { get: vi.fn().mockReturnValue(1) };
        const result = character.attack(dagger, fakeRandom);
        expect(result).toBeDefined();
    });
    describe('With one weapon style active', () => {
        let fakeRandom;
        let result;
        beforeAll(() => {
            fakeRandom = { get: vi.fn().mockReturnValue(1) };
        });
        beforeEach(() => {
            character.toggleEquipItem(Inventory_1.EquipmentName.dagger);
            const attack = character.getAttack(Inventory_1.EquipmentName.dagger);
            result = attack.roll(fakeRandom);
        });
        it('should calculate damage roll result', () => {
            expect(result.damage.rollResult.rolls).toEqual([1]);
            expect(result.damage.rollResult.discartedRolls).toEqual([]);
        });
        it('should have default attribute modifier on damage', () => {
            const modifier = result.damage.modifiers.fixed.get('strength');
            expect(modifier).toBeDefined();
            expect(modifier === null || modifier === void 0 ? void 0 : modifier.baseValue).toBe(2);
        });
        it('should calculate damage total', () => {
            expect(result.damage.total).toBe(3);
        });
        it('should have one weapon style modifier on test', () => {
            const oneWeaponStyleModifier = result.test.modifiers.contextual.get(Power_1.GeneralPowerName.oneWeaponStyle);
            expect(oneWeaponStyleModifier).toBeDefined();
            expect(oneWeaponStyleModifier === null || oneWeaponStyleModifier === void 0 ? void 0 : oneWeaponStyleModifier.baseValue).toBe(2);
            const appliableValue = character.getContextualModifierAppliableValue(oneWeaponStyleModifier);
            expect(appliableValue).toBe(2);
        });
        it('should calculate test total', () => {
            expect(result.test.total).toBe(7);
        });
        it('should sum test modifiers total', () => {
            expect(dagger.getTestModifiersTotal()).toBe(2);
        });
        it('should sum test modifiers max total', () => {
            expect(dagger.getTestModifiersMaxTotal()).toBe(2);
        });
    });
    it('should get dagger attack without one weapon style modifier', () => {
        expect(dagger.getTestModifiersMaxTotal()).toBe(2);
        expect(dagger.getTestModifiersTotal()).toBe(0);
    });
    it('should unselect fight style and remove modifiers', () => {
        const fightStyle = character.getFightStyle();
        expect(fightStyle).toBeDefined();
        character.unselectFightStyle();
        expect(character.getFightStyle()).toBeUndefined();
    });
    it('should have default purpose damage modifier', () => {
        dagger = character.getAttacks().get(Inventory_1.EquipmentName.dagger);
        expect(dagger.getDamageModifiersMaxTotal()).toBe(2);
        expect(dagger.getDamageModifiersTotal()).toBe(2);
    });
    it('should get default test attribute', () => {
        const modifier = dagger.getTestSkillAttributeModifier();
        expect(modifier).toBe(2);
    });
    it('should change test attribute to dexterity', () => {
        dagger.changeTestAttackAttribute('dexterity');
        const modifier = dagger.getTestSkillAttributeModifier();
        expect(modifier).toBe(1);
    });
    it('should throw with invalid skill attribute', () => {
        expect(() => {
            dagger.changeTestAttackAttribute('charisma');
        }).toThrow();
    });
    it('should have triggered special attack', () => {
        const attack = character.getAttacks().get(Inventory_1.EquipmentName.dagger);
        const effects = attack.getTriggeredEffects();
        expect(effects.get(Ability_1.TriggeredEffectName.specialAttack)).toBeDefined();
    });
    it('should have attack cost with disabled triggered effect', () => {
        const attack = character.getAttacks().get(Inventory_1.EquipmentName.dagger);
        const cost = attack.getManaCost();
        expect(cost).toBeDefined();
        expect(cost).toEqual({ type: 'mana', value: 0 });
    });
    it('should have attack cost with enabled triggered effect', () => {
        const attack = character.getAttacks().get(Inventory_1.EquipmentName.dagger);
        attack.enableTriggeredEffect({
            effectName: Ability_1.TriggeredEffectName.specialAttack,
        });
        const cost = attack.getManaCost();
        expect(cost).toBeDefined();
        expect(cost).toEqual({ type: 'mana', value: 1 });
    });
    it('should disable triggered effect', () => {
        const attack = character.getAttacks().get(Inventory_1.EquipmentName.dagger);
        attack.enableTriggeredEffect({
            effectName: Ability_1.TriggeredEffectName.specialAttack,
        });
        attack.disableTriggeredEffect(Ability_1.TriggeredEffectName.specialAttack);
        const cost = attack.getManaCost();
        expect(cost).toBeDefined();
        expect(cost).toEqual({ type: 'mana', value: 0 });
        expect(attack.modifiers.test.fixed.get(Role_1.RoleAbilityName.specialAttack)).toBeUndefined();
    });
});
