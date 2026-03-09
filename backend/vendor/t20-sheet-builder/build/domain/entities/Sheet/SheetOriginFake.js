"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SheetOriginFake = void 0;
class SheetOriginFake {
    constructor(origin = undefined) {
        this.origin = origin;
        this.chooseOrigin = vi.fn();
    }
    getOrigin() {
        return this.origin;
    }
}
exports.SheetOriginFake = SheetOriginFake;
