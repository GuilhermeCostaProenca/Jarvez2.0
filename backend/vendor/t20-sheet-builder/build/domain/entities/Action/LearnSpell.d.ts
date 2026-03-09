import { Action, type ActionSubClassParams } from './Action';
export declare class LearnSpell extends Action<'learnSpell'> {
    constructor(params: ActionSubClassParams<'learnSpell'>);
    execute(): void;
    getDescription(): string;
}
