"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistPathSerializedHandlerSorcerer = void 0;
const ArcanistPath_1 = require("../ArcanistPath");
const ArcanistPathSorcerer_1 = require("../ArcanistPathSorcerer");
const ArcanistLineageSerializedHandler_1 = require("../ArcanistPathSorcerer/ArcanistLineage/ArcanistLineageSerializedHandler");
const ArcanistPathSerializedHandler_1 = require("./ArcanistPathSerializedHandler");
class ArcanistPathSerializedHandlerSorcerer extends ArcanistPathSerializedHandler_1.ArcanistPathSerializedHandler {
    handle(request) {
        const draconic = new ArcanistLineageSerializedHandler_1.ArcanistLineageSerializedHandlerDraconic();
        const faerie = new ArcanistLineageSerializedHandler_1.ArcanistLineageSerializedHandlerFaerie();
        const red = new ArcanistLineageSerializedHandler_1.ArcanistLineageSerializedHandlerRed();
        draconic
            .setNext(faerie)
            .setNext(red);
        const lineage = draconic.execute(request.lineage);
        return new ArcanistPathSorcerer_1.ArcanistPathSorcerer(lineage);
    }
    shouldHandle(request) {
        return request.name === ArcanistPath_1.ArcanistPathName.sorcerer;
    }
}
exports.ArcanistPathSerializedHandlerSorcerer = ArcanistPathSerializedHandlerSorcerer;
