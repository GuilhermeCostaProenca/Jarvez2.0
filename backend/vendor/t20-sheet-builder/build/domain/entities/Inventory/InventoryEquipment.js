"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.InventoryEquipment = void 0;
class InventoryEquipment {
    constructor(equipment, isEquipped = false) {
        this.equipment = equipment;
        this.isEquipped = isEquipped;
        this.quantity = 1;
    }
    toggleEquipped(modifiers) {
        this.isEquipped = !this.isEquipped;
        if (this.isEquipped) {
            this.equipment.onEquip(modifiers);
        }
        if (!this.isEquipped) {
            this.equipment.onUnequip(modifiers);
        }
    }
    getQuantity() {
        return this.quantity;
    }
    increaseQuantity() {
        this.quantity++;
    }
    getIsEquipped() {
        return this.isEquipped;
    }
    serialize() {
        return {
            name: this.equipment.name,
            isEquipped: this.getIsEquipped(),
        };
    }
}
exports.InventoryEquipment = InventoryEquipment;
