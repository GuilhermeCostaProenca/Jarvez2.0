"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Ability_1 = require("../../Ability");
const Character_1 = require("../../Character");
const Inventory_1 = require("../../Inventory");
const Acid_1 = require("../../Inventory/Equipment/EquipmentAlchemic/Prepared/Acid");
const LoveElixir_1 = require("../../Inventory/Equipment/EquipmentAlchemic/Prepared/LoveElixir");
const Accurate_1 = require("../../Inventory/Equipment/EquipmentImprovement/Accurate");
const Fit_1 = require("../../Inventory/Equipment/EquipmentImprovement/Fit");
const Assegai_1 = require("../../Inventory/Equipment/Weapon/OffensiveWeapon/SimpleWeapon/Assegai");
const Sheet_1 = require("../../Sheet");
const SheetBuilder_1 = require("../../Sheet/SheetBuilder");
const Transaction_1 = require("../../Sheet/Transaction");
const Skill_1 = require("../../Skill");
const RoleAbilityName_1 = require("../RoleAbilityName");
const Inventor_1 = require("./Inventor");
describe('Inventor', () => {
    describe('Basic', () => {
        let sheet;
        let transaction;
        let inventor;
        let character;
        beforeEach(() => {
            sheet = new Sheet_1.BuildingSheet();
            const sheetBuilder = new SheetBuilder_1.SheetBuilder(sheet);
            transaction = new Transaction_1.Transaction(sheet);
            inventor = new Inventor_1.Inventor([
                [
                    Skill_1.SkillName.knowledge,
                    Skill_1.SkillName.cure,
                    Skill_1.SkillName.diplomacy,
                    Skill_1.SkillName.fortitude,
                ],
            ], {
                equipment: new Assegai_1.Assegai(),
                improvement: new Accurate_1.Accurate(),
                choice: 'superiorItem',
            });
            sheetBuilder.chooseRole(inventor);
            sheetBuilder.addInitialEquipment({
                money: 10,
                simpleWeapon: new Inventory_1.Dagger(),
                armor: new Inventory_1.LeatherArmor(),
            });
            character = new Character_1.Character(sheet);
        });
        it('should have ingenuity ability', () => {
            expect(sheet.getSheetAbilities().getRoleAbilities().has(RoleAbilityName_1.RoleAbilityName.ingenuity)).toBe(true);
        });
        it('should have ingenuity triggered effect', () => {
            const triggeredEffects = sheet.getSheetTriggeredEffects().getByEvent(Ability_1.TriggerEvent.skillTestExceptAttack);
            expect(triggeredEffects).toHaveLength(1);
        });
        it('should apply ingenuity bonus on skill test', () => {
            character.sheet.getSheetAttributes().increaseAttribute('intelligence', 2);
            const skill = character.getSkill(Skill_1.SkillName.perception);
            const triggeredEffects = skill.getTriggeredEffects();
            const ingenuity = triggeredEffects.get(Ability_1.TriggeredEffectName.ingenuity);
            ingenuity === null || ingenuity === void 0 ? void 0 : ingenuity.enable({
                effectName: Ability_1.TriggeredEffectName.ingenuity,
            });
            const result = skill.roll({
                get: () => 10,
            });
            expect(result.total).toBe(12);
        });
        it('should not apply ingenuity bonus on attack test', () => {
            character.sheet.getSheetAttributes().increaseAttribute('intelligence', 2);
            const attack = character.getAttack(Inventory_1.EquipmentName.dagger);
            expect(attack).toBeDefined();
            expect(attack.getTriggeredEffects().size).toBe(0);
        });
        it('should have prototype ability', () => {
            expect(sheet.getSheetAbilities().getRoleAbilities().has(RoleAbilityName_1.RoleAbilityName.prototype)).toBe(true);
        });
    });
    describe('Prototype with Superior Item', () => {
        it('should have prototype superior item', () => {
            const sheet = new Sheet_1.BuildingSheet();
            const sheetBuilder = new SheetBuilder_1.SheetBuilder(sheet);
            const inventor = new Inventor_1.Inventor([
                [
                    Skill_1.SkillName.knowledge,
                    Skill_1.SkillName.cure,
                    Skill_1.SkillName.diplomacy,
                    Skill_1.SkillName.fortitude,
                ],
            ], {
                equipment: new Assegai_1.Assegai(),
                improvement: new Accurate_1.Accurate(),
                choice: 'superiorItem',
            });
            sheetBuilder.chooseRole(inventor);
            sheetBuilder.addInitialEquipment({
                money: 10,
                simpleWeapon: new Inventory_1.Dagger(),
                armor: new Inventory_1.LeatherArmor(),
            });
            const prototype = sheet.getSheetInventory().getEquipment(Inventory_1.EquipmentName.assegai);
            expect(prototype).toBeDefined();
            expect(prototype === null || prototype === void 0 ? void 0 : prototype.equipment.improvements).toHaveLength(1);
        });
        it('should not accept superior item worthing more than 2000$', () => {
            expect(() => {
                const inventor = new Inventor_1.Inventor([
                    [
                        Skill_1.SkillName.knowledge,
                        Skill_1.SkillName.cure,
                        Skill_1.SkillName.diplomacy,
                        Skill_1.SkillName.fortitude,
                    ],
                ], {
                    equipment: new Inventory_1.FullPlate(),
                    improvement: new Fit_1.Fit(),
                    choice: 'superiorItem',
                });
            }).toThrow('SUPERIOR_ITEM_PRICE_LIMIT_REACHED');
        });
    });
    describe('Prototype with Alchemic Items', () => {
        it('should have prototype alchemic items', () => {
            const sheet = new Sheet_1.BuildingSheet();
            const sheetBuilder = new SheetBuilder_1.SheetBuilder(sheet);
            const inventor = new Inventor_1.Inventor([
                [
                    Skill_1.SkillName.knowledge,
                    Skill_1.SkillName.cure,
                    Skill_1.SkillName.diplomacy,
                    Skill_1.SkillName.fortitude,
                ],
            ], {
                alchemicItems: Array.from({ length: 10 }, () => new Acid_1.Acid()),
                choice: 'alchemicItems',
            });
            sheetBuilder.chooseRole(inventor);
            sheetBuilder.addInitialEquipment({
                money: 10,
                simpleWeapon: new Inventory_1.Dagger(),
                armor: new Inventory_1.LeatherArmor(),
            });
            const prototypeItems = sheet.getSheetInventory().getEquipment(Inventory_1.EquipmentName.acid);
            expect(prototypeItems).toBeDefined();
            expect(prototypeItems === null || prototypeItems === void 0 ? void 0 : prototypeItems.getQuantity()).toBe(10);
        });
        it('should not accept more than 500$ worth of alchemic items', () => {
            expect(() => {
                const items = Array.from({ length: 10 }, () => new LoveElixir_1.LoveElixir());
                const inventor = new Inventor_1.Inventor([
                    [
                        Skill_1.SkillName.knowledge,
                        Skill_1.SkillName.cure,
                        Skill_1.SkillName.diplomacy,
                        Skill_1.SkillName.fortitude,
                    ],
                ], {
                    alchemicItems: items,
                    choice: 'alchemicItems',
                });
            }).toThrow('ALCHEMIC_PRICE_LIMIT_REACHED');
        });
    });
});
