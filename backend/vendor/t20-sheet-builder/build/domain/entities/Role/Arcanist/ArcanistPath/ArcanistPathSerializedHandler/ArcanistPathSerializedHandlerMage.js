"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistPathSerializedHandlerMage = void 0;
const __1 = require("..");
const Spell_1 = require("../../../../Spell");
const ArcanistPathSerializedHandler_1 = require("./ArcanistPathSerializedHandler");
class ArcanistPathSerializedHandlerMage extends ArcanistPathSerializedHandler_1.ArcanistPathSerializedHandler {
    handle(request) {
        const spell = Spell_1.SpellFactory.make(request.extraSpell);
        return new __1.ArcanistPathMage(spell);
    }
    shouldHandle(request) {
        return request.name === __1.ArcanistPathName.mage;
    }
}
exports.ArcanistPathSerializedHandlerMage = ArcanistPathSerializedHandlerMage;
