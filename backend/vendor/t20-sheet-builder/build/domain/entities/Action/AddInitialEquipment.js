"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AddInitialEquipment = void 0;
const Translatable_1 = require("../Translatable");
const Action_1 = require("./Action");
class AddInitialEquipment extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'addInitialEquipment' }));
    }
    execute() {
        const sheetInventory = this.transaction.sheet.getSheetInventory();
        sheetInventory.addInitialEquipment(this.payload, this.transaction);
    }
    getDescription() {
        const simpleWeapon = new Translatable_1.Translatable(this.payload.simpleWeapon.name).getTranslation();
        const armor = this.payload.armor ? new Translatable_1.Translatable(this.payload.armor.name).getTranslation() : undefined;
        const martialWeapon = this.payload.martialWeapon ? new Translatable_1.Translatable(this.payload.martialWeapon.name).getTranslation() : undefined;
        const weapons = `${simpleWeapon}${armor ? `, ${armor}` : ''}${martialWeapon ? `, ${martialWeapon}` : ''}`;
        return `Equipamento inicial adicionado: ${weapons}.`;
    }
}
exports.AddInitialEquipment = AddInitialEquipment;
