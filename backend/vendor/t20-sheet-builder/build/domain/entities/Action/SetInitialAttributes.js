"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SetInitialAttributes = void 0;
const StringHelper_1 = require("../StringHelper");
const Action_1 = require("./Action");
class SetInitialAttributes extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'setInitialAttributes' }));
    }
    execute() {
        const sheetAttributes = this.transaction.sheet.getSheetAttributes();
        sheetAttributes.setInitialAttributes(this.payload.attributes);
    }
    getDescription() {
        const attributesText = StringHelper_1.StringHelper.getAttributesText(this.payload.attributes);
        return `Atributos iniciais: ${attributesText}.`;
    }
}
exports.SetInitialAttributes = SetInitialAttributes;
