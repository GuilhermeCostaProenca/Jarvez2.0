"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const __1 = require("../..");
const Inventory_1 = require("../../Inventory");
const Origin_1 = require("../../Origin");
const Power_1 = require("../../Power");
const Race_1 = require("../../Race");
const Skill_1 = require("../../Skill");
const SheetBuilder_1 = require("../SheetBuilder");
describe('SheetSerializer', () => {
    describe('Human Warrior', () => {
        let sheet;
        let role;
        let race;
        let sheetBuilder;
        let origin;
        let serializedSheet;
        beforeAll(() => {
            const choices = [
                new Race_1.VersatileChoiceSkill(Skill_1.SkillName.acrobatics),
                new Race_1.VersatileChoicePower(new Power_1.OneWeaponStyle()),
            ];
            race = new Race_1.Human(['charisma', 'constitution', 'dexterity'], choices);
            role = new __1.Warrior([[Skill_1.SkillName.fight], [Skill_1.SkillName.aim, Skill_1.SkillName.athletics]]);
            sheetBuilder = new SheetBuilder_1.SheetBuilder();
            origin = new Origin_1.Acolyte([new Origin_1.OriginBenefitGeneralPower(new Power_1.IronWill()), new Origin_1.OriginBenefitSkill(Skill_1.SkillName.cure)]);
            sheet = sheetBuilder
                .setInitialAttributes({ strength: 0, dexterity: 0, charisma: 0, constitution: 0, intelligence: 0, wisdom: 2 })
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
            const context = new __1.OutOfGameContext();
            const serializer = new __1.SheetSerializer(context);
            serializedSheet = serializer.serialize(sheet);
        });
        it('should have origin equipments', () => {
            expect(serializedSheet.equipments).toContainEqual(expect.objectContaining({ name: Inventory_1.EquipmentName.sacredSymbol }));
            expect(serializedSheet.equipments).toContainEqual(expect.objectContaining({ name: Inventory_1.EquipmentName.priestCostume }));
        });
    });
});
