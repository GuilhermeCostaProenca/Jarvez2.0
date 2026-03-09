"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PickGrantedPower = void 0;
const Translatable_1 = require("../Translatable");
const Translator_1 = require("../Translator");
const Action_1 = require("./Action");
class PickGrantedPower extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'pickGrantedPower' }));
    }
    execute() {
        const sheetPowers = this.transaction.sheet.getSheetPowers();
        sheetPowers.pickGrantedPower(this.payload.power, this.transaction, this.payload.source);
    }
    getDescription() {
        const source = new Translatable_1.Translatable(this.payload.source).getTranslation();
        const power = Translator_1.Translator.getPowerTranslation(this.payload.power.name);
        return `${source}: poder ${power} escolhido.`;
    }
}
exports.PickGrantedPower = PickGrantedPower;
