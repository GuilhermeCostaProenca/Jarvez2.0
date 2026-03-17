import type { ContextualModifierInterface } from './ContextualModifierInterface';
import type { ContextualModifiersListInterface } from './ContextualModifiersListInterface';
export declare class ContextualModifiersListFake implements ContextualModifiersListInterface {
    serialize: import("vitest").Mock<any, any>;
    get: import("vitest").Mock<any, any>;
    modifiers: ContextualModifierInterface[];
    total: number;
    maxTotal: number;
    add: import("vitest").Mock<any, any>;
    remove: import("vitest").Mock<any, any>;
    getTotal(): number;
    getMaxTotal(): number;
}
