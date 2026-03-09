import type { ModifierInterface } from '../ModifierInterface';
import type { FixedModifiersListInterface } from './FixedModifiersList';
export declare class FixedModifiersListFake implements FixedModifiersListInterface {
    get: import("vitest").Mock<any, any>;
    modifiers: ModifierInterface[];
    total: number;
    add: import("vitest").Mock<any, any>;
    remove: import("vitest").Mock<any, any>;
    serialize: import("vitest").Mock<any, any>;
    getTotal(): number;
}
