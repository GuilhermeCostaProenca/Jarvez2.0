"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistSerializer = void 0;
const errors_1 = require("../../../../errors");
const RoleSerializer_1 = require("../../RoleSerializer");
const ArcanistPath_1 = require("../ArcanistPath");
/**
* @deprecated Use `arcanist.serialize()` instead
*/
class ArcanistSerializer extends RoleSerializer_1.RoleSerializer {
    constructor(arcanist) {
        super(arcanist);
        this.arcanist = arcanist;
        this.pathSerializer = this.getPathSerializer(arcanist.getPath());
    }
    serializeRole() {
        const path = this.pathSerializer.serialize();
        return {
            name: this.arcanist.name,
            initialSpells: this.arcanist.getInitialSpells().map(spell => spell.name),
            path,
        };
    }
    getPathSerializer(path) {
        if (path instanceof ArcanistPath_1.ArcanistPathMage) {
            return new ArcanistPath_1.ArcanistPathSerializerMage(path);
        }
        if (path instanceof ArcanistPath_1.ArcanistPathSorcerer) {
            return new ArcanistPath_1.ArcanistPathSerializerSorcerer(path);
        }
        if (path instanceof ArcanistPath_1.ArcanistPathWizard) {
            return new ArcanistPath_1.ArcanistPathSerializerWizard(path);
        }
        throw new errors_1.SheetBuilderError('INVALID_PATH');
    }
}
exports.ArcanistSerializer = ArcanistSerializer;
