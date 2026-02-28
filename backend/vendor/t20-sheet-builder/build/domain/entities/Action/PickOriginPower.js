"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PickOriginPower = void 0;
const Translator_1 = require("../Translator");
const Action_1 = require("./Action");
class PickOriginPower extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'pickOriginPower' }));
    }
    execute() {
        const sheetPowers = this.transaction.sheet.getSheetPowers();
        sheetPowers.pickOriginPower(this.payload.power, this.transaction, this.payload.source);
    }
    getDescription() {
        const power = Translator_1.Translator.getPowerTranslation(this.payload.power.name);
        return `Poder de origem: ${power} escolhido.`;
    }
}
exports.PickOriginPower = PickOriginPower;
