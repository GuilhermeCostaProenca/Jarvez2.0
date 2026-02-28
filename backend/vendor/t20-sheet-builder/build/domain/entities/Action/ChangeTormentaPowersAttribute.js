"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ChangeTormentaPowersAttribute = void 0;
const Translatable_1 = require("../Translatable");
const Translator_1 = require("../Translator");
const Action_1 = require("./Action");
class ChangeTormentaPowersAttribute extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'changeTormentaPowersAttribute' }));
    }
    execute() {
        const sheetAttributes = this.transaction.sheet.getSheetAttributes();
        sheetAttributes.changeTormentaPowersAttribute(this.payload.attribute);
    }
    getDescription() {
        const source = new Translatable_1.Translatable(this.payload.source).getTranslation();
        const attribute = Translator_1.Translator.getAttributeTranslation(this.payload.attribute);
        return `${source}: agora você perde ${attribute} por poderes de tormenta.`;
    }
}
exports.ChangeTormentaPowersAttribute = ChangeTormentaPowersAttribute;
