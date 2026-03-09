"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Inventory = void 0;
const Equipment_1 = require("./Equipment");
const Shield_1 = require("./Equipment/Weapon/DefensiveWeapon/Shield/Shield");
const InventoryEquipment_1 = require("./InventoryEquipment");
class Inventory {
    constructor() {
        this.equipments = new Map();
        this.money = 0;
    }
    addEquipment(equipment, isEquipped = false) {
        var _a;
        if (this.equipments.has(equipment.name)) {
            (_a = this.equipments.get(equipment.name)) === null || _a === void 0 ? void 0 : _a.increaseQuantity();
        }
        else {
            this.equipments.set(equipment.name, new InventoryEquipment_1.InventoryEquipment(equipment, isEquipped));
        }
    }
    addMoney(amount) {
        this.money += amount;
    }
    removeMoney(amount) {
        this.money -= amount;
    }
    getItem(name) {
        return this.equipments.get(name);
    }
    getEquipments() {
        return this.equipments;
    }
    getArmor() {
        const found = [...this.equipments.values()].find(item => item.getIsEquipped() && item.equipment instanceof Equipment_1.Armor);
        return found;
    }
    getShield() {
        const found = [...this.equipments.values()].find(item => item.getIsEquipped() && item.equipment instanceof Shield_1.Shield);
        return found;
    }
    getWieldedItems() {
        return Array.from(this.equipments.values())
            .filter(item => item.getIsEquipped() && item.equipment.isWieldable)
            .map(item => item.equipment.name);
    }
    getMoney() {
        return this.money;
    }
}
exports.Inventory = Inventory;
