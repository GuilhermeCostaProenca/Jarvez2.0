import { Action, type ActionSubClassParams } from './Action';
export declare class AddPerLevelModifierToManaPoints extends Action<'addPerLevelModifierToManaPoints'> {
    constructor(params: ActionSubClassParams<'addPerLevelModifierToManaPoints'>);
    execute(): void;
    getDescription(): string;
}
