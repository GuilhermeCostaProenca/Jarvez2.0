"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Translatable = void 0;
const Translator_1 = require("./Translator");
class Translatable {
    constructor(value) {
        this.value = value;
    }
    getTranslation() {
        return Translator_1.Translator.getTranslation(this.value);
    }
}
exports.Translatable = Translatable;
