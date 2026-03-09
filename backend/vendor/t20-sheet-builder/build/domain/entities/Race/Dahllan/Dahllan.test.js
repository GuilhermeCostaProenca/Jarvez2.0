"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const vitest_1 = require("vitest");
const WildEmpathy_1 = require("../../Ability/common/WildEmpathy");
const ApplyRaceAbility_1 = require("../../Action/ApplyRaceAbility");
const Modifier_1 = require("../../Modifier");
const BuildingSheet_1 = require("../../Sheet/BuildingSheet/BuildingSheet");
const Transaction_1 = require("../../Sheet/Transaction");
const Spell_1 = require("../../Spell");
const RaceAbilityName_1 = require("../RaceAbilityName");
const Dahllan_1 = require("./Dahllan");
(0, vitest_1.describe)('Dahllan', () => {
    let sheet;
    let transaction;
    beforeEach(() => {
        sheet = new BuildingSheet_1.BuildingSheet();
        transaction = new Transaction_1.Transaction(sheet);
    });
    (0, vitest_1.it)('should apply +2 to wisdom, +1 to dexterity and -1 to intelligence', () => {
        const dahllan = new Dahllan_1.Dahllan();
        dahllan.addToSheet(transaction);
        (0, vitest_1.expect)(sheet.getSheetAttributes().getValues()).toEqual({
            strength: 0,
            dexterity: 1,
            constitution: 0,
            intelligence: -1,
            wisdom: 2,
            charisma: 0,
        });
    });
    (0, vitest_1.it)('should learn Control Plants', () => {
        const dahllan = new Dahllan_1.Dahllan();
        dahllan.addToSheet(transaction);
        const spells = transaction.sheet.getSheetSpells().getSpells();
        (0, vitest_1.expect)(spells.get(Spell_1.SpellName.controlPlants)).toBeDefined();
    });
    (0, vitest_1.it)('should have Allihanna Armor ability', () => {
        const dahllan = new Dahllan_1.Dahllan();
        dahllan.addToSheet(transaction);
        (0, vitest_1.expect)(transaction.sheet
            .getSheetAbilities()
            .getRaceAbilities()
            .has(RaceAbilityName_1.RaceAbilityName.allihannaArmor)).toBeTruthy();
    });
    (0, vitest_1.it)('should have Wild Empathy ability', () => {
        const dahllan = new Dahllan_1.Dahllan();
        dahllan.addToSheet(transaction);
        (0, vitest_1.expect)(transaction.sheet
            .getSheetAbilities()
            .getRaceAbilities()
            .has(RaceAbilityName_1.RaceAbilityName.wildEmpathy)).toBeTruthy();
    });
    (0, vitest_1.it)('should add animal handling bonus if apply repeated Wild Empathy', () => {
        const dahllan = new Dahllan_1.Dahllan();
        dahllan.addToSheet(transaction);
        transaction.run(new ApplyRaceAbility_1.ApplyRaceAbility({
            payload: {
                ability: new WildEmpathy_1.WildEmpathy(),
                source: RaceAbilityName_1.RaceAbilityName.wildEmpathy,
            },
            transaction,
        }));
        const { animalHandling } = transaction.sheet.getSheetSkills().getSkills();
        (0, vitest_1.expect)(animalHandling.fixedModifiers.modifiers).toHaveLength(1);
        (0, vitest_1.expect)(animalHandling.fixedModifiers.modifiers).toContainEqual(new Modifier_1.FixedModifier(RaceAbilityName_1.RaceAbilityName.wildEmpathy, 2));
    });
});
