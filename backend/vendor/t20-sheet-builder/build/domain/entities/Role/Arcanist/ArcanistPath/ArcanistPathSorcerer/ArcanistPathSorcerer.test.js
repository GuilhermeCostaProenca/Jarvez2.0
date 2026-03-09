"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const DamageType_1 = require("../../../../Damage/DamageType");
const Power_1 = require("../../../../Power");
const Sheet_1 = require("../../../../Sheet");
const Transaction_1 = require("../../../../Sheet/Transaction");
const Skill_1 = require("../../../../Skill");
const Spell_1 = require("../../../../Spell");
const RoleAbilityName_1 = require("../../../RoleAbilityName");
const ArcanistLineageDraconic_1 = require("./ArcanistLineage/ArcanistLineageDraconic/ArcanistLineageDraconic");
const ArcanistLineageFaerie_1 = require("./ArcanistLineage/ArcanistLineageFaerie/ArcanistLineageFaerie");
const ArcanistLineageRed_1 = require("./ArcanistLineage/ArcanistLineageRed/ArcanistLineageRed");
const ArcanistPathSorcerer_1 = require("./ArcanistPathSorcerer");
describe('ArcanistPathSorcerer', () => {
    let sheet;
    let transaction;
    beforeEach(() => {
        sheet = new Sheet_1.BuildingSheet();
        transaction = new Transaction_1.Transaction(sheet);
    });
    it('should create sorcerer with draconic lineage', () => {
        const lineage = new ArcanistLineageDraconic_1.ArcanistLineageDraconic(DamageType_1.DamageType.fire);
        const arcanistPath = new ArcanistPathSorcerer_1.ArcanistPathSorcerer(lineage);
        arcanistPath.addToSheet(transaction);
        const lifeModifier = sheet.getSheetLifePoints().getFixedModifiers().get(RoleAbilityName_1.RoleAbilityName.arcanistSupernaturalLineage);
        expect(lifeModifier).toBeDefined();
        expect(lifeModifier === null || lifeModifier === void 0 ? void 0 : lifeModifier.attributeBonuses).toContain('charisma');
    });
    it('should create sorcerer with faerie lineage', () => {
        const spell = new Spell_1.IllusoryDisguise();
        const lineage = new ArcanistLineageFaerie_1.ArcanistLineageFaerie(spell);
        const arcanistPath = new ArcanistPathSorcerer_1.ArcanistPathSorcerer(lineage);
        transaction.sheet.getSheetSpells().learnCircle(Spell_1.SpellCircle.first, 'arcane');
        arcanistPath.addToSheet(transaction);
        expect(sheet.getSheetSpells().getSpells().get(spell.name)).toBeDefined();
        expect(sheet.getSkills()[Skill_1.SkillName.cheat].skill.getIsTrained()).toBe(true);
    });
    it('should create sorcerer with red lineage', () => {
        const power = new Power_1.Shell();
        const lineage = new ArcanistLineageRed_1.ArcanistLineageRed(power, 'wisdom');
        const arcanistPath = new ArcanistPathSorcerer_1.ArcanistPathSorcerer(lineage);
        arcanistPath.addToSheet(transaction);
        expect(sheet.getSheetAttributes().getTormentaPowersAttribute()).toBe('wisdom');
        expect(sheet.getSheetPowers().getGeneralPowers().get(power.name)).toBeDefined();
    });
});
