"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Ability_1 = require("../../Ability");
const Character_1 = require("../../Character");
const Sheet_1 = require("../../Sheet");
const Transaction_1 = require("../../Sheet/Transaction");
const Skill_1 = require("../../Skill");
const RoleAbilityName_1 = require("../RoleAbilityName");
const RoleName_1 = require("../RoleName");
const Buccaneer_1 = require("./Buccaneer");
describe('buccaneer', () => {
    let sheet;
    let transaction;
    let buccaneer;
    let character;
    beforeEach(() => {
        sheet = new Sheet_1.BuildingSheet();
        transaction = new Transaction_1.Transaction(sheet);
        buccaneer = new Buccaneer_1.Buccaneer([
            [Skill_1.SkillName.fight],
            [
                Skill_1.SkillName.aim,
                Skill_1.SkillName.acting,
                Skill_1.SkillName.perception,
                Skill_1.SkillName.gambling,
            ],
        ]);
        buccaneer.addToSheet(transaction);
        character = new Character_1.Character(sheet);
    });
    it('should have reflexes trained', () => {
        const skills = sheet.getSkills();
        expect(skills[Skill_1.SkillName.reflexes].skill.getIsTrained()).toBe(true);
    });
    it('should dispatch profiencies add', () => {
        const proficiencies = transaction.sheet.getSheetProficiencies().getProficiencies();
        expect(proficiencies).toContain(Sheet_1.Proficiency.martial);
    });
    it('should dispatch life points fixed modifier add', () => {
        const lifePoints = sheet.getSheetLifePoints();
        const fixedModifier = lifePoints.getFixedModifiers().get(RoleName_1.RoleName.buccaneer);
        expect(fixedModifier).toBeDefined();
        expect(fixedModifier === null || fixedModifier === void 0 ? void 0 : fixedModifier.baseValue).toBe(16);
    });
    it('should dispatch life points per level modifier add', () => {
        const lifePoints = sheet.getSheetLifePoints();
        const perLevelModifier = lifePoints.getPerLevelModifiers().get(RoleName_1.RoleName.buccaneer);
        expect(perLevelModifier).toBeDefined();
        expect(perLevelModifier === null || perLevelModifier === void 0 ? void 0 : perLevelModifier.baseValue).toBe(4);
        expect(perLevelModifier === null || perLevelModifier === void 0 ? void 0 : perLevelModifier.includeFirstLevel).toBe(false);
    });
    it('should dispatch mana points modifiers add', () => {
        const manaPoints = sheet.getSheetManaPoints();
        const perLevelModifier = manaPoints.getPerLevelModifiers().get(RoleName_1.RoleName.buccaneer);
        expect(perLevelModifier).toBeDefined();
        expect(perLevelModifier === null || perLevelModifier === void 0 ? void 0 : perLevelModifier.baseValue).toBe(3);
        expect(perLevelModifier === null || perLevelModifier === void 0 ? void 0 : perLevelModifier.includeFirstLevel).toBe(true);
    });
    describe('audacity', () => {
        it('should add audacity ability', () => {
            const abilities = sheet.getSheetAbilities();
            expect(abilities.getRoleAbilities().get(RoleAbilityName_1.RoleAbilityName.audacity)).toBeDefined();
        });
        it('should have audacity as testExceptAttack triggered effect', () => {
            const effects = sheet.getSheetTriggeredEffects().getByEvent(Ability_1.TriggerEvent.skillTestExceptAttack);
            const audacity = effects.get(Ability_1.TriggeredEffectName.audacity);
            expect(audacity).toBeDefined();
        });
        it('should enable audacity triggered effect', () => {
            const skill = character.getSkills()[Skill_1.SkillName.gambling];
            skill.enableTriggeredEffect({
                attributes: sheet.getSheetAttributes().getValues(),
                effectName: Ability_1.TriggeredEffectName.audacity,
            });
            const triggeredEffect = skill.triggeredEffects.get(Ability_1.TriggeredEffectName.audacity);
            expect(triggeredEffect === null || triggeredEffect === void 0 ? void 0 : triggeredEffect.getIsEnabled()).toBe(true);
        });
        it('should add skill modifier when audacity is enabled', () => {
            const skill = character.getSkills()[Skill_1.SkillName.gambling];
            skill.enableTriggeredEffect({
                attributes: sheet.getSheetAttributes().getValues(),
                effectName: Ability_1.TriggeredEffectName.audacity,
            });
            expect(skill.getFixedModifier('skillExceptAttack', RoleAbilityName_1.RoleAbilityName.audacity)).toBeDefined();
        });
        it('should roll skill test with audacity', () => {
            character.sheet.getSheetAttributes().increaseAttribute('charisma', 2);
            const skill = character.getSkills()[Skill_1.SkillName.stealth];
            skill.enableTriggeredEffect({
                attributes: sheet.getSheetAttributes().getValues(),
                effectName: Ability_1.TriggeredEffectName.audacity,
            });
            const roll = skill.roll({ get: () => 10 });
            expect(roll.modifiers.fixed.get(RoleAbilityName_1.RoleAbilityName.audacity)).toBeDefined();
            expect(roll.modifiersTotal).toBe(2);
            expect(roll.total).toBe(12);
        });
        it('should disable audacity triggered effect', () => {
            const skill = character.getSkills()[Skill_1.SkillName.gambling];
            skill.enableTriggeredEffect({
                attributes: sheet.getSheetAttributes().getValues(),
                effectName: Ability_1.TriggeredEffectName.audacity,
            });
            skill.disableTriggeredEffect(Ability_1.TriggeredEffectName.audacity);
            const triggeredEffect = skill.triggeredEffects.get(Ability_1.TriggeredEffectName.audacity);
            expect(triggeredEffect === null || triggeredEffect === void 0 ? void 0 : triggeredEffect.getIsEnabled()).toBe(false);
            expect(skill.getFixedModifier('skillExceptAttack', RoleAbilityName_1.RoleAbilityName.audacity)).toBeUndefined();
        });
    });
});
