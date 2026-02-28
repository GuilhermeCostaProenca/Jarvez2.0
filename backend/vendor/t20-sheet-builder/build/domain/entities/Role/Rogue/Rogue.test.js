"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Ability_1 = require("../../Ability");
const Character_1 = require("../../Character");
const Sheet_1 = require("../../Sheet");
const SheetBuilder_1 = require("../../Sheet/SheetBuilder");
const Transaction_1 = require("../../Sheet/Transaction");
const Skill_1 = require("../../Skill");
const RoleAbilityName_1 = require("../RoleAbilityName");
const Rogue_1 = require("./Rogue");
describe('Rogue', () => {
    let rogue;
    let sheet;
    let transaction;
    const chosenSkills = [
        [
            Skill_1.SkillName.acrobatics,
            Skill_1.SkillName.athletics,
            Skill_1.SkillName.acting,
            Skill_1.SkillName.animalRide,
            Skill_1.SkillName.knowledge,
            Skill_1.SkillName.diplomacy,
            Skill_1.SkillName.cheat,
            Skill_1.SkillName.stealth,
        ],
    ];
    describe('Basic', () => {
        beforeEach(() => {
            rogue = new Rogue_1.Rogue(chosenSkills, new Set([Skill_1.SkillName.reflexes]));
            sheet = new Sheet_1.BuildingSheet();
            transaction = new Transaction_1.Transaction(sheet);
            rogue.addToSheet(transaction);
        });
        it('should have sneak attack ability', () => {
            const roleAbilities = sheet.getSheetAbilities().getRoleAbilities();
            expect(roleAbilities.get(RoleAbilityName_1.RoleAbilityName.sneakAttack)).toBeDefined();
        });
        it('should have specialist ability', () => {
            const roleAbilities = sheet.getSheetAbilities().getRoleAbilities();
            expect(roleAbilities.get(RoleAbilityName_1.RoleAbilityName.specialist)).toBeDefined();
        });
        it('should have specialist skill', () => {
            const roleAbilities = sheet.getSheetAbilities().getRoleAbilities();
            const specialist = roleAbilities.get(RoleAbilityName_1.RoleAbilityName.specialist);
            const specialistSkills = specialist.getSkills();
            expect(specialistSkills).toHaveLength(1);
        });
    });
    describe('Specialist', () => {
        it('should throw if doesn\'t receive specialist skill with 0 intelligence', () => {
            const rogue = new Rogue_1.Rogue(chosenSkills, new Set());
            const builder = new SheetBuilder_1.SheetBuilder();
            expect(() => {
                builder.chooseRole(rogue);
            }).toThrow('INVALID_SPECIALIST_SKILLS_SIZE');
        });
        it('should throw if receive different specialist skills size for intelligence bigger than 0', () => {
            const rogue = new Rogue_1.Rogue(chosenSkills, new Set([Skill_1.SkillName.reflexes, Skill_1.SkillName.stealth, Skill_1.SkillName.athletics]));
            const builder = new SheetBuilder_1.SheetBuilder();
            builder.getBuildingSheet().getSheetAttributes().increaseAttribute('intelligence', 2);
            expect(() => {
                builder.chooseRole(rogue);
            }).toThrow('INVALID_SPECIALIST_SKILLS_SIZE');
        });
        it('should throw if specialist skills are not trained', () => {
            const rogue = new Rogue_1.Rogue(chosenSkills, new Set([Skill_1.SkillName.reflexes, Skill_1.SkillName.aim]));
            const builder = new SheetBuilder_1.SheetBuilder();
            builder.getBuildingSheet().getSheetAttributes().increaseAttribute('intelligence', 2);
            expect(() => {
                builder.chooseRole(rogue);
            }).toThrow('INVALID_SPECIALIST_SKILLS_NOT_TRAINED');
        });
        it('should have specialist triggered effect', () => {
            const rogue = new Rogue_1.Rogue(chosenSkills, new Set([Skill_1.SkillName.reflexes]));
            const builder = new SheetBuilder_1.SheetBuilder();
            builder.chooseRole(rogue);
            const sheet = builder.getBuildingSheet();
            const triggeredEffects = sheet.getSheetTriggeredEffects().getByEvent(Ability_1.TriggerEvent.skillTestExceptAttack);
            expect(triggeredEffects.get(Ability_1.TriggeredEffectName.specialist)).toBeDefined();
        });
        it('should add skill modifier when enabled', () => {
            const rogue = new Rogue_1.Rogue(chosenSkills, new Set([Skill_1.SkillName.reflexes]));
            const builder = new SheetBuilder_1.SheetBuilder();
            builder.chooseRole(rogue);
            const sheet = builder.getBuildingSheet();
            const character = new Character_1.Character(sheet);
            const skill = character.getSkill(Skill_1.SkillName.reflexes);
            expect(skill.getModifiersTotal()).toBe(0);
            skill.enableTriggeredEffect({ effectName: Ability_1.TriggeredEffectName.specialist, skill });
            const modifier = skill.getFixedModifier('skillExceptAttack', RoleAbilityName_1.RoleAbilityName.specialist);
            expect(modifier).toBeDefined();
            expect(modifier === null || modifier === void 0 ? void 0 : modifier.baseValue).toBe(skill.getTrainingPoints());
            expect(skill.getModifiersTotal()).toBe(skill.getTrainingPoints());
        });
    });
});
