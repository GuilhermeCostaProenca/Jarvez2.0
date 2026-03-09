"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AttributeRequirement = void 0;
const StringHelper_1 = require("../../StringHelper");
const Translator_1 = require("../../Translator");
const Requirement_1 = require("./Requirement");
class AttributeRequirement extends Requirement_1.Requirement {
    constructor(attribute, value) {
        super();
        this.attribute = attribute;
        this.value = value;
        this.description = this.getDescription();
    }
    verify(sheet) {
        const attributes = sheet.getSheetAttributes().getValues();
        return attributes[this.attribute] >= this.value;
    }
    getDescription() {
        return `${Translator_1.Translator.getAttributeTranslation(this.attribute)} ${StringHelper_1.StringHelper.addNumberSign(this.value)}`;
    }
}
exports.AttributeRequirement = AttributeRequirement;
