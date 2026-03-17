"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RoleSerializer = void 0;
/**
* @deprecated Use `role.serialize()` instead
*/
class RoleSerializer {
    constructor(role) {
        this.role = role;
    }
    serialize() {
        const serialized = this.role.serialize();
        return serialized;
    }
}
exports.RoleSerializer = RoleSerializer;
