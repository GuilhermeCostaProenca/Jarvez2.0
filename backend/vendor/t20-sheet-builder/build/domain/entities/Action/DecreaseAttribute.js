"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DecreaseAttribute = void 0;
const Translatable_1 = require("../Translatable");
const Translator_1 = require("../Translator");
const Action_1 = require("./Action");
class DecreaseAttribute extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'decreaseAttribute' }));
    }
    execute() {
        const sheetAttributes = this.transaction.sheet.getSheetAttributes();
        sheetAttributes.decreaseAttribute(this.payload.attribute, this.payload.quantity);
    }
    getDescription() {
        const source = new Translatable_1.Translatable(this.payload.source).getTranslation();
        const attribute = Translator_1.Translator.getAttributeTranslation(this.payload.attribute);
        return `${source}: -${this.payload.quantity} em ${attribute}.`;
    }
}
exports.DecreaseAttribute = DecreaseAttribute;
