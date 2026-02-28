"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistPathHandlerMage = void 0;
const errors_1 = require("../../../../../errors");
const Spell_1 = require("../../../../Spell");
const ArcanistPath_1 = require("../ArcanistPath");
const ArcanistPathMage_1 = require("../ArcanistPathMage");
const ArcanistPathHandler_1 = require("./ArcanistPathHandler");
class ArcanistPathHandlerMage extends ArcanistPathHandler_1.ArcanistPathHandler {
    handle(request) {
        if (!request.mageSpell) {
            throw new errors_1.SheetBuilderError('MISSING_MAGE_SPELL');
        }
        const spell = Spell_1.SpellFactory.make(request.mageSpell);
        return new ArcanistPathMage_1.ArcanistPathMage(spell);
    }
    shouldHandle(request) {
        return request.path === ArcanistPath_1.ArcanistPathName.mage;
    }
}
exports.ArcanistPathHandlerMage = ArcanistPathHandlerMage;
