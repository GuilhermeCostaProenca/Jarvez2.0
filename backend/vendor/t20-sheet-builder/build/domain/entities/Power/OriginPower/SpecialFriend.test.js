"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const BuildingSheet_1 = require("../../Sheet/BuildingSheet/BuildingSheet");
const Transaction_1 = require("../../Sheet/Transaction");
const SkillName_1 = require("../../Skill/SkillName");
const OriginPowerName_1 = require("./OriginPowerName");
const SpecialFriend_1 = require("./SpecialFriend");
describe('SpecialFriend', () => {
    let sheet;
    let transaction;
    beforeEach(() => {
        sheet = new BuildingSheet_1.BuildingSheet();
        transaction = new Transaction_1.Transaction(sheet);
    });
    it('should dispatch animalHandling modifier add', () => {
        const specialFriend = new SpecialFriend_1.SpecialFriend(SkillName_1.SkillName.acrobatics);
        specialFriend.addToSheet(transaction);
        const skillModifier = sheet.getSkills()[SkillName_1.SkillName.animalHandling].skill.fixedModifiers.get(OriginPowerName_1.OriginPowerName.specialFriend);
        expect(skillModifier).toBeDefined();
        expect(skillModifier === null || skillModifier === void 0 ? void 0 : skillModifier.baseValue).toBe(5);
    });
    it('should dispatch custom skill modifier add', () => {
        const specialFriend = new SpecialFriend_1.SpecialFriend(SkillName_1.SkillName.acrobatics);
        specialFriend.addToSheet(transaction);
        const skillModifier = sheet.getSkills()[SkillName_1.SkillName.acrobatics].skill.fixedModifiers.get(OriginPowerName_1.OriginPowerName.specialFriend);
        expect(skillModifier).toBeDefined();
        expect(skillModifier === null || skillModifier === void 0 ? void 0 : skillModifier.baseValue).toBe(2);
    });
    it('should not allow custom skill to be fight', () => {
        expect(() => {
            const specialFriend = new SpecialFriend_1.SpecialFriend(SkillName_1.SkillName.fight);
        }).toThrow('INVALID_SKILL');
    });
    it('should not allow custom skill to be aim', () => {
        expect(() => {
            const specialFriend = new SpecialFriend_1.SpecialFriend(SkillName_1.SkillName.aim);
        }).toThrow('INVALID_SKILL');
    });
});
