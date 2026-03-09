import { Action, type ActionSubClassParams } from './Action';
export declare class AddPerLevelModifierToLifePoints extends Action<'addPerLevelModifierToLifePoints'> {
    constructor(params: ActionSubClassParams<'addPerLevelModifierToLifePoints'>);
    execute(): void;
    getDescription(): string;
}
