"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Ability_1 = require("../Ability");
const Character_1 = require("../Character");
const Context_1 = require("../Context");
const Inventory_1 = require("../Inventory");
const Origin_1 = require("../Origin");
const Power_1 = require("../Power");
const Race_1 = require("../Race");
const Role_1 = require("../Role");
const Buccaneer_1 = require("../Role/Buccaneer/Buccaneer");
const Skill_1 = require("../Skill");
const BuildingSheet_1 = require("./BuildingSheet");
const SheetAttributes_1 = require("./SheetAttributes");
const SheetBuilder_1 = require("./SheetBuilder");
describe('SheetSkills', () => {
    describe('Human Warrior', () => {
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
        });
        it('should be serialized', () => {
            const sheet = new BuildingSheet_1.BuildingSheet();
            const context = new Context_1.OutOfGameContext();
            const serialized = sheet.getSheetSkills().serialize(sheet, context);
            expect(serialized.intelligenceSkills).toHaveLength(0);
        });
        it('should get related attribute modifier', () => {
            const sheetSkills = character.sheet.getSkills();
            const result = sheetSkills[Skill_1.SkillName.survival].getAttributeModifier();
            expect(result).toBe(2);
        });
        it('should calculate total modifiers', () => {
            const sheetSkills = character.sheet.getSkills();
            const result = sheetSkills[Skill_1.SkillName.survival].getModifiersTotal();
            expect(result).toBe(2);
        });
        it('should roll skill', () => {
            const sheetSkills = character.sheet.getSkills();
            const result = sheetSkills[Skill_1.SkillName.survival].roll({
                get: vi.fn().mockReturnValue(10),
            });
            expect(result.total).toBe(12);
        });
        it('should roll trained skill', () => {
            const sheetSkills = character.sheet.getSkills();
            sheetSkills[Skill_1.SkillName.survival].skill.train();
            const result = sheetSkills[Skill_1.SkillName.survival].roll({
                get: vi.fn().mockReturnValue(10),
            });
            expect(result.total).toBe(14);
        });
    });
    describe('Human buccaneer', () => {
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
            role = new Buccaneer_1.Buccaneer([
                [Skill_1.SkillName.fight],
                [Skill_1.SkillName.aim,
                    Skill_1.SkillName.acting,
                    Skill_1.SkillName.perception,
                    Skill_1.SkillName.gambling],
            ]);
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
        it('should get skill with attribute modifier', () => {
            const sheetSkills = character.getSkills();
            const result = sheetSkills[Skill_1.SkillName.gambling].getAttributeModifier();
            expect(result).toBe(1);
        });
        it('should roll skill with attribute modifier', () => {
            const skill = character.getSkill(Skill_1.SkillName.intimidation);
            const result = skill.roll({
                get: vi.fn().mockReturnValue(10),
            });
            expect(result.total).toBe(11);
            expect(skill.getTotalBaseModifier()).toBe(1);
        });
        it('should roll skill with attribute modifier getting all skills', () => {
            const sheetSkills = character.getSkills();
            const result = sheetSkills[Skill_1.SkillName.intimidation].roll({
                get: vi.fn().mockReturnValue(10),
            });
            expect(result.total).toBe(11);
            expect(sheetSkills.intimidation.getTotalBaseModifier()).toBe(1);
        });
        it('should get skill triggered effects', () => {
            var _a;
            const sheetSkills = character.getSkills();
            const effects = sheetSkills[Skill_1.SkillName.gambling].getTriggeredEffects();
            expect(effects.get(Ability_1.TriggeredEffectName.audacity)).toBeDefined();
            expect((_a = effects.get(Ability_1.TriggeredEffectName.audacity)) === null || _a === void 0 ? void 0 : _a.getIsEnabled()).toBe(false);
        });
        it('should enable skill triggered effect', () => {
            var _a;
            const sheetSkills = character.getSkills();
            sheetSkills[Skill_1.SkillName.gambling].enableTriggeredEffect({
                effectName: Ability_1.TriggeredEffectName.audacity,
                attributes: Object.assign(Object.assign({}, SheetAttributes_1.SheetAttributes.initial), { charisma: 2 }),
            });
            const effects = sheetSkills[Skill_1.SkillName.gambling].getTriggeredEffects();
            expect(effects.get(Ability_1.TriggeredEffectName.audacity)).toBeDefined();
            expect((_a = effects.get(Ability_1.TriggeredEffectName.audacity)) === null || _a === void 0 ? void 0 : _a.getIsEnabled()).toBe(true);
        });
        it('should disable skill triggered effect', () => {
            var _a;
            const sheetSkills = character.getSkills();
            sheetSkills[Skill_1.SkillName.gambling].enableTriggeredEffect({
                effectName: Ability_1.TriggeredEffectName.audacity,
                attributes: Object.assign(Object.assign({}, SheetAttributes_1.SheetAttributes.initial), { charisma: 2 }),
            });
            sheetSkills[Skill_1.SkillName.gambling].disableTriggeredEffect(Ability_1.TriggeredEffectName.audacity);
            const effects = sheetSkills[Skill_1.SkillName.gambling].getTriggeredEffects();
            expect(effects.get(Ability_1.TriggeredEffectName.audacity)).toBeDefined();
            expect((_a = effects.get(Ability_1.TriggeredEffectName.audacity)) === null || _a === void 0 ? void 0 : _a.getIsEnabled()).toBe(false);
        });
    });
});
