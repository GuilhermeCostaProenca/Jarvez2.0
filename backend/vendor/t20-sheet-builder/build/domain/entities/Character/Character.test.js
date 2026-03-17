"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Inventory_1 = require("../Inventory");
const Origin_1 = require("../Origin");
const Power_1 = require("../Power");
const Race_1 = require("../Race");
const Role_1 = require("../Role");
const SheetBuilder_1 = require("../Sheet/SheetBuilder");
const Skill_1 = require("../Skill");
const Character_1 = require("./Character");
describe('Character', () => {
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
        character.toggleEquipItem(Inventory_1.EquipmentName.lightShield);
    });
    it('should get trained skill', () => {
        expect(character.sheet.getSheetSkills().getSkill(Skill_1.SkillName.fight).getIsTrained()).toBeTruthy();
    });
    it('should get untrained skill', () => {
        expect(character.sheet.getSheetSkills().getSkill(Skill_1.SkillName.animalHandling).getIsTrained()).toBeFalsy();
    });
    it('should have fight style', () => {
        expect(character.getFightStyle()).toBeDefined();
    });
    it('should toggle wield item', () => {
        expect(character.getWieldedItems()).toEqual([]);
        character.toggleEquipItem(Inventory_1.EquipmentName.dagger);
        expect(character.getWieldedItems()).toEqual([Inventory_1.EquipmentName.dagger]);
        character.toggleEquipItem(Inventory_1.EquipmentName.dagger);
        expect(character.getWieldedItems()).toEqual([]);
    });
});
