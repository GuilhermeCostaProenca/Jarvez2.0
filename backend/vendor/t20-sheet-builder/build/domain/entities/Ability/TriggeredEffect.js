"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.TriggeredEffect = exports.TriggerEvent = void 0;
const ActivateableAbilityEffect_1 = require("./ActivateableAbilityEffect");
var TriggerEvent;
(function (TriggerEvent) {
    TriggerEvent["attack"] = "attack";
    TriggerEvent["defend"] = "defend";
    TriggerEvent["skillTest"] = "skillTest";
    TriggerEvent["skillTestExceptAttack"] = "skillTestExceptAttack";
    TriggerEvent["resistanceTest"] = "resistanceTest";
})(TriggerEvent || (exports.TriggerEvent = TriggerEvent = {}));
class TriggeredEffect extends ActivateableAbilityEffect_1.ActivateableAbilityEffect {
    get activationType() {
        return 'triggered';
    }
    constructor(params) {
        super(params);
        this.triggerEvents = Array.isArray(params.triggerEvents)
            ? params.triggerEvents
            : [params.triggerEvents];
        this.name = params.name;
    }
    serialize() {
        return Object.assign(Object.assign({}, super.serialize()), { triggerEvents: this.triggerEvents, name: this.name });
    }
}
exports.TriggeredEffect = TriggeredEffect;
