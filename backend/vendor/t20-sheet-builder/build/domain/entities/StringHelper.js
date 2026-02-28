"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.StringHelper = void 0;
const Capitalizer_1 = require("./Capitalizer");
const TextSeparatorGenerator_1 = require("./TextSeparatorGenerator");
const Translator_1 = require("./Translator");
class StringHelper {
    static capitalize(string) {
        return Capitalizer_1.Capitalizer.capitalize(string);
    }
    static addNumberSign(number) {
        return number >= 0 ? `+${number}` : String(number);
    }
    static getAttributesText(attributes) {
        return Object.entries(attributes).reduce((acc, [attribute, value], index, array) => {
            const separator = TextSeparatorGenerator_1.TextSeparatorGenerator.generateSeparator(index, array.length);
            const translatedAttribute = Translator_1.Translator.getAttributeTranslation(attribute);
            const modifierWithSign = StringHelper.addNumberSign(value);
            return acc + `${modifierWithSign} ${translatedAttribute}${separator}`;
        }, '');
    }
}
exports.StringHelper = StringHelper;
