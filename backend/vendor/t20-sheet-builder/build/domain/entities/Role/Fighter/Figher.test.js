"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const SheetBuilder_1 = require("../../Sheet/SheetBuilder");
const SkillName_1 = require("../../Skill/SkillName");
const RoleAbilityName_1 = require("../RoleAbilityName");
const Fighter_1 = require("./Fighter");
describe('Fighter', () => {
    let sheet;
    beforeEach(() => {
        const figher = new Fighter_1.Fighter([
            [
                SkillName_1.SkillName.acrobatics,
                SkillName_1.SkillName.animalHandling,
                SkillName_1.SkillName.athletics,
                SkillName_1.SkillName.cheat,
            ],
        ]);
        const builder = new SheetBuilder_1.SheetBuilder();
        builder.chooseRole(figher);
        sheet = builder.getBuildingSheet();
    });
    it('should have Fight ability', () => {
        const abilities = sheet.getSheetAbilities().getRoleAbilities();
        const fight = abilities.get(RoleAbilityName_1.RoleAbilityName.fight);
        expect(fight).toBeDefined();
    });
    it('should have Lightning Strike ability', () => {
        const abilities = sheet.getSheetAbilities().getRoleAbilities();
        const fight = abilities.get(RoleAbilityName_1.RoleAbilityName.lightningStrike);
        expect(fight).toBeDefined();
    });
});
