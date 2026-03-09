import { Action, type ActionSubClassParams } from './Action';
export declare class SetInitialAttributes extends Action<'setInitialAttributes'> {
    constructor(params: ActionSubClassParams<'setInitialAttributes'>);
    execute(): void;
    getDescription(): string;
}
