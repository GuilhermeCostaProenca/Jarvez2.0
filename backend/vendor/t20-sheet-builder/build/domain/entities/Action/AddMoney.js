"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AddMoney = void 0;
const Translatable_1 = require("../Translatable");
const Action_1 = require("./Action");
class AddMoney extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'addMoney' }));
    }
    execute() {
        const sheetInventory = this.transaction.sheet.getSheetInventory();
        sheetInventory.addMoney(this.payload.quantity);
    }
    getDescription() {
        const source = new Translatable_1.Translatable(this.payload.source).getTranslation();
        const value = this.payload.quantity.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        return `${source}: +T$${value}.`;
    }
}
exports.AddMoney = AddMoney;
