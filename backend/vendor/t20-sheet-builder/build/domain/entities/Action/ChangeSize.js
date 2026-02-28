"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ChangeSize = void 0;
const Translator_1 = require("../Translator");
const Translatable_1 = require("../Translatable");
const Action_1 = require("./Action");
class ChangeSize extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'changeSize' }));
    }
    execute() {
        const sheetSize = this.transaction.sheet.getSheetSize();
        sheetSize.changeSize(this.payload.size);
    }
    getDescription() {
        const source = new Translatable_1.Translatable(this.payload.source).getTranslation();
        return `${source}: tamanho alterado para ${Translator_1.Translator.getSizeTranslation(this.payload.size.name)}.`;
    }
}
exports.ChangeSize = ChangeSize;
