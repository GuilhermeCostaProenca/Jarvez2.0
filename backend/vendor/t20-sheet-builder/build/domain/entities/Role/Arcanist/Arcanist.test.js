"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const __1 = require("../..");
const DamageType_1 = require("../../Damage/DamageType");
const Sheet_1 = require("../../Sheet");
const Transaction_1 = require("../../Sheet/Transaction");
const SkillName_1 = require("../../Skill/SkillName");
const ArcaneArmor_1 = require("../../Spell/ArcaneArmor/ArcaneArmor");
const FlamesExplosion_1 = require("../../Spell/FlamesExplosion/FlamesExplosion");
const IllusoryDisguise_1 = require("../../Spell/IllusoryDisguise/IllusoryDisguise");
const MentalDagger_1 = require("../../Spell/MentalDagger/MentalDagger");
const ArcanistBuider_1 = require("./ArcanistBuider");
const ArcanistPath_1 = require("./ArcanistPath");
const ArcanistPathWizard_1 = require("./ArcanistPath/ArcanisPathWizard/ArcanistPathWizard");
const ArcanistPathWizardFocusWand_1 = require("./ArcanistPath/ArcanisPathWizard/ArcanistPathWizardFocusWand");
const ArcanistPathMage_1 = require("./ArcanistPath/ArcanistPathMage/ArcanistPathMage");
const ArcanistLineage_1 = require("./ArcanistPath/ArcanistPathSorcerer/ArcanistLineage");
describe('Arcanist', () => {
    let sheet;
    let transaction;
    beforeEach(() => {
        sheet = new Sheet_1.BuildingSheet();
        transaction = new Transaction_1.Transaction(sheet);
    });
    it('should dispatch proper train skills', () => {
        const arcanist = ArcanistBuider_1.ArcanistBuilder
            .chooseSkills([[SkillName_1.SkillName.knowledge, SkillName_1.SkillName.diplomacy]])
            .choosePath(new ArcanistPathMage_1.ArcanistPathMage(new FlamesExplosion_1.FlamesExplosion()))
            .chooseSpells([new ArcaneArmor_1.ArcaneArmor(), new IllusoryDisguise_1.IllusoryDisguise(), new MentalDagger_1.MentalDagger()]);
        arcanist.addToSheet(transaction);
        const skills = transaction.sheet.getSkills();
        expect(skills[SkillName_1.SkillName.knowledge].skill.getIsTrained()).toBe(true);
        expect(skills[SkillName_1.SkillName.diplomacy].skill.getIsTrained()).toBe(true);
        expect(skills[SkillName_1.SkillName.will].skill.getIsTrained()).toBe(true);
        expect(skills[SkillName_1.SkillName.mysticism].skill.getIsTrained()).toBe(true);
    });
    it('should not train with missing chooses', () => {
        expect(() => {
            const arcanist = ArcanistBuider_1.ArcanistBuilder
                .chooseSkills([[SkillName_1.SkillName.knowledge]])
                .choosePath(new ArcanistPathMage_1.ArcanistPathMage(new FlamesExplosion_1.FlamesExplosion()))
                .chooseSpells([new ArcaneArmor_1.ArcaneArmor(), new IllusoryDisguise_1.IllusoryDisguise(), new MentalDagger_1.MentalDagger()]);
        }).toThrow('MISSING_ROLE_SKILLS');
    });
    it('should not train with wrong skills', () => {
        expect(() => {
            const arcanist = ArcanistBuider_1.ArcanistBuilder
                .chooseSkills([[SkillName_1.SkillName.knowledge, SkillName_1.SkillName.athletics]])
                .choosePath(new ArcanistPathMage_1.ArcanistPathMage(new FlamesExplosion_1.FlamesExplosion()))
                .chooseSpells([new ArcaneArmor_1.ArcaneArmor(), new IllusoryDisguise_1.IllusoryDisguise(), new MentalDagger_1.MentalDagger()]);
        }).toThrow('INVALID_CHOSEN_SKILLS');
    });
    it('should not dispatch profiency add', () => {
        const arcanist = ArcanistBuider_1.ArcanistBuilder
            .chooseSkills([[SkillName_1.SkillName.knowledge, SkillName_1.SkillName.diplomacy]])
            .choosePath(new ArcanistPathMage_1.ArcanistPathMage(new FlamesExplosion_1.FlamesExplosion()))
            .chooseSpells([new ArcaneArmor_1.ArcaneArmor(), new IllusoryDisguise_1.IllusoryDisguise(), new MentalDagger_1.MentalDagger()]);
        arcanist.addToSheet(transaction);
        const proficiencies = transaction.sheet.getSheetProficiencies().getProficiencies();
        expect(proficiencies).toHaveLength(2);
    });
    it('should learn spells', () => {
        const arcanist = ArcanistBuider_1.ArcanistBuilder
            .chooseSkills([[SkillName_1.SkillName.knowledge, SkillName_1.SkillName.diplomacy]])
            .choosePath(new ArcanistPathMage_1.ArcanistPathMage(new FlamesExplosion_1.FlamesExplosion()))
            .chooseSpells([new ArcaneArmor_1.ArcaneArmor(), new IllusoryDisguise_1.IllusoryDisguise(), new MentalDagger_1.MentalDagger()]);
        arcanist.addToSheet(transaction);
        const spells = transaction.sheet.getSheetSpells().getSpells();
        expect(spells.has(ArcaneArmor_1.ArcaneArmor.spellName)).toBeTruthy();
        expect(spells.has(MentalDagger_1.MentalDagger.spellName)).toBeTruthy();
        expect(spells.has(IllusoryDisguise_1.IllusoryDisguise.spellName)).toBeTruthy();
    });
    describe('Mage', () => {
        let arcanist;
        let mageSheet;
        let mageTransaction;
        beforeEach(() => {
            arcanist = ArcanistBuider_1.ArcanistBuilder
                .chooseSkills([[SkillName_1.SkillName.knowledge, SkillName_1.SkillName.diplomacy]])
                .choosePath(new ArcanistPathMage_1.ArcanistPathMage(new FlamesExplosion_1.FlamesExplosion()))
                .chooseSpells([new ArcaneArmor_1.ArcaneArmor(), new IllusoryDisguise_1.IllusoryDisguise(), new MentalDagger_1.MentalDagger()]);
            mageSheet = new Sheet_1.BuildingSheet();
            mageTransaction = new Transaction_1.Transaction(mageSheet);
            arcanist.addToSheet(mageTransaction);
        });
        it('should have intelligence as key attribute', () => {
            expect(arcanist.getSpellsAttribute()).toBe('intelligence');
        });
        it('should learn all levels', () => {
            expect(arcanist.getSpellLearnFrequency()).toBe('all');
        });
        it('should learn additional spell', () => {
            const spells = mageSheet.getSheetSpells().getSpells();
            expect(spells.has(__1.SpellName.flamesExplosion)).toBeTruthy();
        });
        it('should have mana modifier', () => {
            const modifiers = mageSheet.getSheetManaPoints().getFixedModifiers();
            const manaModifier = modifiers.get(__1.RoleAbilityName.arcanistSpells);
            expect(manaModifier).toBeDefined();
        });
    });
    describe('Wizard', () => {
        let arcanist;
        let wizardSheet;
        let wizardTransaction;
        beforeEach(() => {
            arcanist = ArcanistBuider_1.ArcanistBuilder
                .chooseSkills([[SkillName_1.SkillName.knowledge, SkillName_1.SkillName.diplomacy]])
                .choosePath(new ArcanistPathWizard_1.ArcanistPathWizard(new ArcanistPathWizardFocusWand_1.ArcanistPathWizardFocusWand()))
                .chooseSpells([new ArcaneArmor_1.ArcaneArmor(), new IllusoryDisguise_1.IllusoryDisguise(), new MentalDagger_1.MentalDagger()]);
            wizardSheet = new Sheet_1.BuildingSheet();
            wizardTransaction = new Transaction_1.Transaction(wizardSheet);
            arcanist.addToSheet(wizardTransaction);
        });
        it('should have intelligence as key attribute', () => {
            expect(arcanist.getSpellsAttribute()).toBe('intelligence');
        });
        it('should learn all levels', () => {
            expect(arcanist.getSpellLearnFrequency()).toBe('all');
        });
        it('should dispatch add focus', () => {
            const equipments = wizardSheet.getSheetInventory().getEquipments();
            expect(equipments.has(__1.EquipmentName.wand)).toBeTruthy();
        });
        it('should have mana modifier', () => {
            const modifiers = wizardSheet.getSheetManaPoints().getFixedModifiers();
            const manaModifier = modifiers.get(__1.RoleAbilityName.arcanistSpells);
            expect(manaModifier).toBeDefined();
            expect(manaModifier === null || manaModifier === void 0 ? void 0 : manaModifier.attributeBonuses).toEqual(['intelligence']);
        });
    });
    describe('Sorcerer', () => {
        let arcanist;
        let sorcererSheet;
        let sorcererTransaction;
        beforeEach(() => {
            const lineage = new ArcanistLineage_1.ArcanistLineageDraconic(DamageType_1.DamageType.fire);
            arcanist = ArcanistBuider_1.ArcanistBuilder
                .chooseSkills([[SkillName_1.SkillName.knowledge, SkillName_1.SkillName.diplomacy]])
                .choosePath(new ArcanistPath_1.ArcanistPathSorcerer(lineage))
                .chooseSpells([new ArcaneArmor_1.ArcaneArmor(), new IllusoryDisguise_1.IllusoryDisguise(), new MentalDagger_1.MentalDagger()]);
            sorcererSheet = new Sheet_1.BuildingSheet();
            sorcererTransaction = new Transaction_1.Transaction(sorcererSheet);
            arcanist.addToSheet(sorcererTransaction);
        });
        it('should have charisma as key attribute', () => {
            expect(arcanist.getSpellsAttribute()).toBe('charisma');
        });
        it('should have mana modifier', () => {
            const modifiers = sorcererSheet.getSheetManaPoints().getFixedModifiers();
            const manaModifier = modifiers.get(__1.RoleAbilityName.arcanistSpells);
            expect(manaModifier).toBeDefined();
            expect(manaModifier === null || manaModifier === void 0 ? void 0 : manaModifier.attributeBonuses).toEqual(['charisma']);
        });
    });
});
