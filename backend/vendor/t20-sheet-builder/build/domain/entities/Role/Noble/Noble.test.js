"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const SheetBuilder_1 = require("../../Sheet/SheetBuilder");
const Skill_1 = require("../../Skill");
const RoleAbilityName_1 = require("../RoleAbilityName");
const Noble_1 = require("./Noble");
describe('Noble', () => {
    let sheet;
    beforeEach(() => {
        const noble = new Noble_1.Noble([
            [Skill_1.SkillName.diplomacy],
            [Skill_1.SkillName.acting, Skill_1.SkillName.animalRide, Skill_1.SkillName.aim, Skill_1.SkillName.animalHandling],
        ]);
        const builder = new SheetBuilder_1.SheetBuilder();
        builder.chooseRole(noble);
        sheet = builder.getBuildingSheet();
    });
    it('should have will trained', () => {
        expect(sheet.getSkill(Skill_1.SkillName.will).isTrained()).toBe(true);
    });
    it('should have self confidence', () => {
        const ability = sheet
            .getSheetAbilities()
            .getRoleAbilities()
            .get(RoleAbilityName_1.RoleAbilityName.selfConfidence);
        expect(ability).toBeDefined();
    });
    it('should have asset', () => {
        const ability = sheet
            .getSheetAbilities()
            .getRoleAbilities()
            .get(RoleAbilityName_1.RoleAbilityName.asset);
        expect(ability).toBeDefined();
    });
});
