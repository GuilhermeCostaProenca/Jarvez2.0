"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AddEquipment = void 0;
const Translatable_1 = require("../Translatable");
const Action_1 = require("./Action");
class AddEquipment extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'addEquipment' }));
    }
    execute() {
        const sheetInventory = this.transaction.sheet.getSheetInventory();
        sheetInventory.addEquipment(this.payload.equipment, this.payload.isEquipped);
    }
    getDescription() {
        const source = new Translatable_1.Translatable(this.payload.source).getTranslation();
        const equipment = new Translatable_1.Translatable(this.payload.equipment.name).getTranslation();
        return `${source}: ${equipment} adicionado ao inventário.`;
    }
}
exports.AddEquipment = AddEquipment;
