"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RegisterTriggeredEffect = void 0;
const Translatable_1 = require("../Translatable");
const Action_1 = require("./Action");
class RegisterTriggeredEffect extends Action_1.Action {
    constructor(params) {
        super(Object.assign(Object.assign({}, params), { type: 'registerTriggeredEffect' }));
    }
    execute() {
        const effects = this.transaction.sheet.getSheetTriggeredEffects();
        effects.registerEffect(this.payload.events, this.payload.effect);
    }
    getDescription() {
        const source = new Translatable_1.Translatable(this.payload.effect.source).getTranslation();
        return `${source}: habilidade engatilhada.`;
    }
}
exports.RegisterTriggeredEffect = RegisterTriggeredEffect;
