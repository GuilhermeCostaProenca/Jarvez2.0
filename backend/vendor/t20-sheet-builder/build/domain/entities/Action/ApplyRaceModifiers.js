"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ApplyRaceModifiers = void 0;
const StringHelper_1 = require("../StringHelper");
const Action_1 = require("./Action");
class ApplyRaceModifiers extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'applyRaceModifiers' }));
    }
    execute() {
        const sheetAttributes = this.transaction.sheet.getSheetAttributes();
        sheetAttributes.applyRaceModifiers(this.payload.modifiers);
    }
    getDescription() {
        const modifiersText = StringHelper_1.StringHelper.getAttributesText(this.payload.modifiers);
        return `Modificadores de raça aplicados: ${modifiersText}.`;
    }
}
exports.ApplyRaceModifiers = ApplyRaceModifiers;
