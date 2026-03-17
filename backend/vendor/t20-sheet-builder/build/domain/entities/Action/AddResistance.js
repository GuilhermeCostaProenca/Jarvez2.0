"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AddResistance = void 0;
const Translatable_1 = require("../Translatable");
const Action_1 = require("./Action");
class AddResistance extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'addResistance' }));
    }
    execute() {
        const { resistance, source, value } = this.payload;
        const resistances = this.transaction.sheet.getSheetResistences();
        resistances.addResistance(resistance, value, source);
    }
    getDescription() {
        const source = new Translatable_1.Translatable(this.payload.source).getTranslation();
        const resistance = new Translatable_1.Translatable(this.payload.resistance).getTranslation();
        return `${source}: você ganha resistência a ${resistance} de +${this.payload.value}.`;
    }
}
exports.AddResistance = AddResistance;
