"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SheetInventory = void 0;
const errors_1 = require("../../errors");
const AddEquipment_1 = require("../Action/AddEquipment");
const AddMoney_1 = require("../Action/AddMoney");
const Inventory_1 = require("../Inventory");
const EquipmentAdventure_1 = require("../Inventory/Equipment/EquipmentAdventure/EquipmentAdventure");
const LightShield_1 = require("../Inventory/Equipment/Weapon/DefensiveWeapon/Shield/LightShield");
const Inventory_2 = require("../Inventory/Inventory");
const Proficiency_1 = require("./Proficiency");
class SheetInventory {
    constructor(inventory = new Inventory_2.Inventory()) {
        this.inventory = inventory;
    }
    serializeInitialEquipment() {
        var _a, _b;
        if (!this.initialEquipment) {
            return;
        }
        return {
            simpleWeapon: this.initialEquipment.simpleWeapon.serialize(),
            martialWeapon: (_a = this.initialEquipment.martialWeapon) === null || _a === void 0 ? void 0 : _a.serialize(),
            armor: (_b = this.initialEquipment.armor) === null || _b === void 0 ? void 0 : _b.serialize(),
            money: this.initialEquipment.money,
        };
    }
    serialize() {
        const equipments = [];
        this.getEquipments().forEach(inventoryEquipment => {
            equipments.push(inventoryEquipment.serialize());
        });
        return equipments;
    }
    getArmorBonus() {
        var _a, _b;
        return (_b = (_a = this.getArmor()) === null || _a === void 0 ? void 0 : _a.equipment.defenseBonus) !== null && _b !== void 0 ? _b : 0;
    }
    getShieldBonus() {
        var _a, _b;
        return (_b = (_a = this.getShield()) === null || _a === void 0 ? void 0 : _a.equipment.defenseBonus) !== null && _b !== void 0 ? _b : 0;
    }
    toggleEquippedItem({ maxWieldedItems, modifiers, name }) {
        const item = this.getEquipment(name);
        if (!item) {
            throw new errors_1.SheetBuilderError('ITEM_NOT_FOUND');
        }
        const wieldedItems = this.getWieldedItems();
        if (item.equipment.isWieldable && !item.getIsEquipped() && maxWieldedItems <= wieldedItems.length) {
            throw new errors_1.SheetBuilderError('MAX_WIELDED_ITEMS');
        }
        item.toggleEquipped(modifiers);
    }
    addEquipment(equipment, isEquipped = false) {
        this.inventory.addEquipment(equipment, isEquipped);
    }
    addInitialEquipment(params, transaction) {
        this.validateInitialWeapons(params, transaction.sheet.getSheetProficiencies());
        this.initialEquipment = params;
        const source = 'default';
        transaction.run(new AddEquipment_1.AddEquipment({ payload: { equipment: new EquipmentAdventure_1.EquipmentAdventure(Inventory_1.EquipmentName.backpack), source }, transaction }));
        transaction.run(new AddEquipment_1.AddEquipment({ payload: { equipment: new EquipmentAdventure_1.EquipmentAdventure(Inventory_1.EquipmentName.travelerCostume), source }, transaction }));
        transaction.run(new AddEquipment_1.AddEquipment({ payload: { equipment: new EquipmentAdventure_1.EquipmentAdventure(Inventory_1.EquipmentName.sleepingBag), source }, transaction }));
        transaction.run(new AddEquipment_1.AddEquipment({ payload: { equipment: params.simpleWeapon, source }, transaction }));
        if (params.martialWeapon) {
            transaction.run(new AddEquipment_1.AddEquipment({ payload: { equipment: params.martialWeapon, source }, transaction }));
        }
        if (params.armor) {
            transaction.run(new AddEquipment_1.AddEquipment({ payload: { equipment: params.armor, isEquipped: true, source }, transaction }));
        }
        if (params.role.proficiencies.includes(Proficiency_1.Proficiency.shield)) {
            transaction.run(new AddEquipment_1.AddEquipment({ payload: { equipment: new LightShield_1.LightShield(), isEquipped: true, source }, transaction }));
        }
        transaction.run(new AddMoney_1.AddMoney({ payload: { quantity: params.money, source }, transaction }));
    }
    getArmor() {
        return this.inventory.getArmor();
    }
    getShield() {
        return this.inventory.getShield();
    }
    addMoney(quantity) {
        this.inventory.addMoney(quantity);
    }
    removeMoney(quantity) {
        this.inventory.removeMoney(quantity);
    }
    getMoney() {
        return this.inventory.getMoney();
    }
    getEquipment(name) {
        return this.inventory.getItem(name);
    }
    getWieldedItems() {
        return this.inventory.getWieldedItems();
    }
    getEquipments() {
        return this.inventory.getEquipments();
    }
    validateInitialWeapons(params, proficiencies) {
        const hasMartialProficiency = proficiencies.has(Proficiency_1.Proficiency.martial);
        if (hasMartialProficiency && !params.martialWeapon) {
            throw new errors_1.SheetBuilderError('MISSING_MARTIAL_WEAPON');
        }
        if (!hasMartialProficiency && params.martialWeapon) {
            throw new errors_1.SheetBuilderError('UNEXPECTED_MARTIAL_WEAPON');
        }
        if (params.role.startsWithArmor && !params.armor) {
            throw new errors_1.SheetBuilderError('MISSING_ARMOR');
        }
        if (!params.role.startsWithArmor && params.armor) {
            throw new errors_1.SheetBuilderError('UNEXPECTED_ARMOR');
        }
        if (params.armor) {
            const hasHeavyArmorProficiency = proficiencies.has(Proficiency_1.Proficiency.heavyArmor);
            const allowedArmors = hasHeavyArmorProficiency
                ? SheetInventory.initialArmorsForHeavyProficients
                : SheetInventory.initialArmors;
            if (!allowedArmors.has(params.armor.name)) {
                throw new errors_1.SheetBuilderError('INVALID_CHOOSED_ARMOR');
            }
        }
    }
}
exports.SheetInventory = SheetInventory;
SheetInventory.initialArmors = new Set([Inventory_1.EquipmentName.leatherArmor, Inventory_1.EquipmentName.studdedLeather]);
SheetInventory.initialArmorsForHeavyProficients = new Set([Inventory_1.EquipmentName.leatherArmor, Inventory_1.EquipmentName.studdedLeather, Inventory_1.EquipmentName.brunea]);
